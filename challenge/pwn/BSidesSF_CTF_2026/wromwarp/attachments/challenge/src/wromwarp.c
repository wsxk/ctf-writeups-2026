/* wromwarp -- A Lonely Entertainment System (LES) Emulator + Debugger */

/*
 * LES System Notes (high-level hardware + ISA reference)
 *
 * Machine hardware:
 * - CPU: 8-bit "L80"-style execution model.
 * - WRAM: 256 bytes (addressed by 8-bit memory pointer registers).
 * - ROM: 4096 instruction words
 * - VRAM: 32x32 monochrome pixel matrix.
 * - Text output: 32-character single-line display.
 * - Input: 6 controller bits (U/D/L/R/A/B).
 *
 * Register model:
 * - General purpose: gA, gB, gC, gD.
 * - Input registers: iU, iD, iL, iR, iA, iB.
 * - Memory pointers: mR (read pointer), mW (write pointer).
 * - Pixel registers: pA, pB.
 * - Cursor pairs: cX1/cY1 and cX2/cY2 for VRAM coordinates.
 * - Control registers: PC (program counter), SPC1..SPC4 (4-level saved return
 *   addresses for CALL/RET), SPCN (active call depth), CMP flag, and ISC
 *   (64-bit instruction counter, debugger-only).
 *
 * Core instruction families:
 * - Data movement:
 *   SET dst, imm-or-reg
 *   DUPE src, dst
 *   LOAD dst          ; dst <- WRAM[mR]
 *   STORE src         ; WRAM[mW] <- src
 *
 * - ALU:
 *   ADD/SUB a, b, dst
 *   INC/DEC src, dst
 *   CMP a, b          ; sets CMP flag (<, =, >)
 *   RND dst           ; dst <- random byte (0..255)
 *   SHIFTL/SHIFTR a, b, dst
 *   AND/OR/XOR a, b, dst
 *
 * - Control flow:
 *   JMP/JMPE/JMPNE/JMPGT/JMPLT/JMPGE/JMPLE <label>
 *   CALL <label>
 *   RET
 *
 * - System/display:
 *   INIT, HALT, INPUT, PRINT, GETP, SETP, CLEAR, DRAW, SLEEP
 *
 * Frame-buffer semantics:
 * - display = front buffer (what is currently shown on screen).
 * - vram    = back buffer (what SETP/CLEAR modify).
 * - GETP reads from display, so logic always sees the last DRAWn frame.
 * - SETP writes to vram, staging next-frame pixel values.
 * - DRAW copies vram -> display to present the staged frame.
 *
 * LES quirks/constraints:
 * - Arithmetic and general registers are 8-bit unsigned; values wrap 0..255.
 * - cX1/cY1/cX2/cY2 are masked to 5 bits on write (range 0..31).
 * - Input regs iU/iD/iL/iR/iA/iB are read-only to ROM code and are set
 *   only by INPUT.
 * - CALL/RET depth is fixed to 4 levels (SPC1..SPC4 tracked by SPCN).
 * - Labels are case-insensitive (normalized uppercase) and max length is 20.
 * - TRAP is an explicit software breakpoint; debugger can toggle trap handling.
 * - SLEEP is processed in short chunks so run-mode break input stays responsive;
 *   breaking during SLEEP ends that instruction early.
 * - ISC is a debugger-only 64-bit instruction counter, not addressable by LES.
 * - Execution hard-stops when ISC reaches LES_ISC_LIMIT until /reset.
 *
 * Execution model in this file:
 * - .les text is tokenized into Instruction records plus a label map.
 * - The execution loop dispatches on opcode with a switch.
 * - PC increments after each successful instruction unless the instruction
 *   explicitly changes control flow (jump/call/ret/init) or halts.
 * - Debugger UI runs in ncurses with:
 *   left pane   : source listing with current-PC arrow and breakpoints
 *   right pane  : 32x32 display + 1x32 text box
 *   bottom pane : REPL for /commands (/load, /break, /run, /step, ...)
 */

#include <ctype.h>
#include <locale.h>
#include <ncurses.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>
#include <wchar.h>

#define LES_ROM_SIZE 4096
#define LES_RAM_SIZE 256
#define LES_TEXT_SIZE 32
#define LES_SCREEN_SIZE 32
#define LES_MAX_ARGS 4
#define LES_MAX_TOKEN 64
#define LES_MAX_LABELS 256
#define LES_MAX_LINE 256
#define LES_MAX_LOGO_LINES 256
#define LES_MAX_LOGO_COLS 512
#define LES_MAX_LABEL_NAME 20
#define LES_ISC_LIMIT 500000000ULL
#define LES_ROM_DIR "roms"

typedef enum {
    OP_SET,
    OP_DUPE,
    OP_LOAD,
    OP_STORE,
    OP_ADD,
    OP_SUB,
    OP_INC,
    OP_DEC,
    OP_CMP,
    OP_RND,
    OP_SHIFTL,
    OP_SHIFTR,
    OP_AND,
    OP_OR,
    OP_XOR,
    OP_JMP,
    OP_JMPE,
    OP_JMPNE,
    OP_JMPGT,
    OP_JMPLT,
    OP_JMPGE,
    OP_JMPLE,
    OP_CALL,
    OP_RET,
    OP_INIT,
    OP_HALT,
    OP_INPUT,
    OP_PRINT,
    OP_GETP,
    OP_SETP,
    OP_CLEAR,
    OP_DRAW,
    OP_SLEEP,
    OP_TRAP,
    OP_INVALID
} OpCode;

typedef enum {
    REG_GA,
    REG_GB,
    REG_GC,
    REG_GD,
    REG_IU,
    REG_ID,
    REG_IL,
    REG_IR,
    REG_IA,
    REG_IB,
    REG_MR,
    REG_MW,
    REG_CX1,
    REG_CY1,
    REG_CX2,
    REG_CY2,
    REG_PA,
    REG_PB,
    REG_COUNT
} RegisterId;

typedef struct {
    OpCode op;
    int argc;
    char args[LES_MAX_ARGS][LES_MAX_TOKEN];
    int line_no;
    char label[LES_MAX_TOKEN];
    char source[LES_MAX_LINE];
} Instruction;

typedef struct {
    char name[LES_MAX_TOKEN];
    int addr;
} Label;

typedef struct {
    Instruction rom[LES_ROM_SIZE];
    int rom_count;
    Label labels[LES_MAX_LABELS];
    int label_count;
    char loaded_path[LES_MAX_LINE];
} Program;

typedef struct {
    uint8_t regs[REG_COUNT];
    uint8_t ram[LES_RAM_SIZE];
    uint8_t vram[LES_SCREEN_SIZE][LES_SCREEN_SIZE];
    uint8_t display[LES_SCREEN_SIZE][LES_SCREEN_SIZE];
    char text[LES_TEXT_SIZE + 1];
    int pc;
    int spc[4];
    int spcn;
    int cmp_flag;
    uint64_t isc;
    bool isc_locked;
    bool halted;
} CPU;

typedef struct {
    WINDOW *asm_win;
    WINDOW *regs_win;
    WINDOW *screen_win;
    WINDOW *text_win;
    WINDOW *repl_win;
} Ui;

typedef struct {
    Program program;
    CPU cpu;
    bool loaded;
    bool breakpoints[LES_ROM_SIZE];
    char last_cmd[LES_MAX_LINE];
    char status[LES_MAX_LINE];
} Emulator;

static bool g_in_run_mode = false;
static bool g_async_break_requested = false;
static bool g_trap_requested = false;
static bool g_traps_enabled = true;
static int g_forward_key = ERR;

static void apply_input_key(CPU *cpu, int key) {
    switch (key) {
    case KEY_UP:
        cpu->regs[REG_IU] = 1;
        break;
    case KEY_DOWN:
        cpu->regs[REG_ID] = 1;
        break;
    case KEY_LEFT:
        cpu->regs[REG_IL] = 1;
        break;
    case KEY_RIGHT:
        cpu->regs[REG_IR] = 1;
        break;
    case '0':
    case KEY_IC:
        cpu->regs[REG_IB] = 1;
        break;
    case '.':
    case KEY_DC:
        cpu->regs[REG_IA] = 1;
        break;
    default:
        break;
    }
}

static char *trim(char *s) {
    while (isspace((unsigned char)*s)) {
        s++;
    }
    if (*s == '\0') {
        return s;
    }
    char *end = s + strlen(s) - 1;
    while (end > s && isspace((unsigned char)*end)) {
        *end-- = '\0';
    }
    return s;
}

static void uppercase(char *s) {
    while (*s) {
        *s = (char)toupper((unsigned char)*s);
        s++;
    }
}

static bool parse_number(const char *tok, uint8_t *out) {
    char *end = NULL;
    long n = 0;
    if (tok[0] == '$') {
        n = strtol(tok + 1, &end, 16);
    } else {
        n = strtol(tok, &end, 0);
    }
    if (end == tok || *end != '\0') {
        return false;
    }
    *out = (uint8_t)(n & 0xff);
    return true;
}

static bool parse_number_long(const char *tok, long *out) {
    char *end = NULL;
    long n = 0;
    if (tok[0] == '$') {
        n = strtol(tok + 1, &end, 16);
    } else {
        n = strtol(tok, &end, 0);
    }
    if (end == tok || *end != '\0') {
        return false;
    }
    *out = n;
    return true;
}

static OpCode parse_opcode(const char *op) {
    if (!strcmp(op, "SET")) return OP_SET;
    if (!strcmp(op, "DUPE")) return OP_DUPE;
    if (!strcmp(op, "LOAD")) return OP_LOAD;
    if (!strcmp(op, "STORE")) return OP_STORE;
    if (!strcmp(op, "ADD")) return OP_ADD;
    if (!strcmp(op, "SUB")) return OP_SUB;
    if (!strcmp(op, "INC")) return OP_INC;
    if (!strcmp(op, "DEC")) return OP_DEC;
    if (!strcmp(op, "CMP")) return OP_CMP;
    if (!strcmp(op, "RND")) return OP_RND;
    if (!strcmp(op, "SHIFTL")) return OP_SHIFTL;
    if (!strcmp(op, "SHIFTR")) return OP_SHIFTR;
    if (!strcmp(op, "AND")) return OP_AND;
    if (!strcmp(op, "OR")) return OP_OR;
    if (!strcmp(op, "XOR")) return OP_XOR;
    if (!strcmp(op, "JMP")) return OP_JMP;
    if (!strcmp(op, "JMPE")) return OP_JMPE;
    if (!strcmp(op, "JMPNE")) return OP_JMPNE;
    if (!strcmp(op, "JMPGT")) return OP_JMPGT;
    if (!strcmp(op, "JMPLT")) return OP_JMPLT;
    if (!strcmp(op, "JMPGE")) return OP_JMPGE;
    if (!strcmp(op, "JMPLE")) return OP_JMPLE;
    if (!strcmp(op, "CALL")) return OP_CALL;
    if (!strcmp(op, "RET")) return OP_RET;
    if (!strcmp(op, "INIT")) return OP_INIT;
    if (!strcmp(op, "HALT")) return OP_HALT;
    if (!strcmp(op, "INPUT")) return OP_INPUT;
    if (!strcmp(op, "PRINT")) return OP_PRINT;
    if (!strcmp(op, "GETP")) return OP_GETP;
    if (!strcmp(op, "SETP")) return OP_SETP;
    if (!strcmp(op, "CLEAR")) return OP_CLEAR;
    if (!strcmp(op, "DRAW")) return OP_DRAW;
    if (!strcmp(op, "SLEEP")) return OP_SLEEP;
    if (!strcmp(op, "TRAP")) return OP_TRAP;
    return OP_INVALID;
}

static int parse_register(const char *name) {
    if (!strcmp(name, "GA")) return REG_GA;
    if (!strcmp(name, "GB")) return REG_GB;
    if (!strcmp(name, "GC")) return REG_GC;
    if (!strcmp(name, "GD")) return REG_GD;
    if (!strcmp(name, "IU")) return REG_IU;
    if (!strcmp(name, "ID")) return REG_ID;
    if (!strcmp(name, "IL")) return REG_IL;
    if (!strcmp(name, "IR")) return REG_IR;
    if (!strcmp(name, "IA")) return REG_IA;
    if (!strcmp(name, "IB")) return REG_IB;
    if (!strcmp(name, "MR")) return REG_MR;
    if (!strcmp(name, "MW")) return REG_MW;
    if (!strcmp(name, "CX1")) return REG_CX1;
    if (!strcmp(name, "CY1")) return REG_CY1;
    if (!strcmp(name, "CX2")) return REG_CX2;
    if (!strcmp(name, "CY2")) return REG_CY2;
    if (!strcmp(name, "PA")) return REG_PA;
    if (!strcmp(name, "PB")) return REG_PB;
    return -1;
}

static const char *reg_name(RegisterId reg) {
    switch (reg) {
    case REG_GA: return "gA";
    case REG_GB: return "gB";
    case REG_GC: return "gC";
    case REG_GD: return "gD";
    case REG_IU: return "iU";
    case REG_ID: return "iD";
    case REG_IL: return "iL";
    case REG_IR: return "iR";
    case REG_IA: return "iA";
    case REG_IB: return "iB";
    case REG_MR: return "mR";
    case REG_MW: return "mW";
    case REG_CX1: return "cX1";
    case REG_CY1: return "cY1";
    case REG_CX2: return "cX2";
    case REG_CY2: return "cY2";
    case REG_PA: return "pA";
    case REG_PB: return "pB";
    case REG_COUNT: return "??";
    }
    return "??";
}

static int label_lookup(const Program *p, const char *name) {
    for (int i = 0; i < p->label_count; i++) {
        if (!strcmp(p->labels[i].name, name)) {
            return p->labels[i].addr;
        }
    }
    return -1;
}

static const char *label_at_addr(const Program *p, int addr) {
    for (int i = 0; i < p->label_count; i++) {
        if ((int)p->labels[i].addr == addr) {
            return p->labels[i].name;
        }
    }
    return NULL;
}

static bool resolve_label_ref(const Program *p, const char *tok, int *target) {
    size_t len = strlen(tok);
    char label[LES_MAX_TOKEN];

    if (len < 3 || tok[0] != '<' || tok[len - 1] != '>') {
        return false;
    }
    if (len - 2 >= sizeof(label)) {
        return false;
    }

    memcpy(label, tok + 1, len - 2);
    label[len - 2] = '\0';
    *target = label_lookup(p, label);
    return *target >= 0;
}

static bool add_label(Program *p, const char *name, int addr) {
    if (p->label_count >= LES_MAX_LABELS) {
        return false;
    }
    if (strlen(name) > LES_MAX_LABEL_NAME) {
        return false;
    }
    if (label_lookup(p, name) >= 0) {
        return false;
    }
    strncpy(p->labels[p->label_count].name, name, LES_MAX_TOKEN - 1);
    p->labels[p->label_count].name[LES_MAX_TOKEN - 1] = '\0';
    p->labels[p->label_count].addr = addr;
    p->label_count++;
    return true;
}

static bool parse_instruction(char *line, Instruction *inst, int line_no, const char *source_line) {
    inst->line_no = line_no;
    inst->argc = 0;
    inst->label[0] = '\0';
    strncpy(inst->source, source_line, LES_MAX_LINE - 1);
    inst->source[LES_MAX_LINE - 1] = '\0';

    char *op = strtok(line, " \t");
    if (!op) {
        return false;
    }
    uppercase(op);
    inst->op = parse_opcode(op);
    if (inst->op == OP_INVALID) {
        return false;
    }

    char *args = strtok(NULL, "");
    if (!args) {
        return true;
    }

    args = trim(args);
    if (*args == '\0') {
        return true;
    }

    char *cursor = args;
    while (true) {
        char *comma = strchr(cursor, ',');
        if (comma) {
            *comma = '\0';
        }

        char *clean = trim(cursor);
        if (*clean == '\0' || inst->argc >= LES_MAX_ARGS) {
            return false;
        }

        uppercase(clean);
        strncpy(inst->args[inst->argc], clean, LES_MAX_TOKEN - 1);
        inst->args[inst->argc][LES_MAX_TOKEN - 1] = '\0';
        inst->argc++;

        if (!comma) {
            break;
        }
        cursor = comma + 1;
    }
    return true;
}

static bool normalize_label_token(const char *tok, char *out, size_t out_len) {
    size_t len = strlen(tok);
    if (len == 0 || out_len == 0) {
        return false;
    }

    if (tok[0] == '<' && tok[len - 1] == '>') {
        if (len <= 2 || len - 1 >= out_len) {
            return false;
        }
        memcpy(out, tok + 1, len - 2);
        out[len - 2] = '\0';
    } else {
        if (len >= out_len) {
            return false;
        }
        memcpy(out, tok, len + 1);
    }

    uppercase(out);
    return out[0] != '\0';
}

static bool valid_rom_name(const char *name) {
    size_t len = strlen(name);
    if (len < 5 || len > 36) {
        return false;
    }
    if (strcmp(name + len - 4, ".les") != 0) {
        return false;
    }

    size_t stem_len = len - 4;
    if (stem_len < 1 || stem_len > 32) {
        return false;
    }
    for (size_t i = 0; i < stem_len; i++) {
        if (name[i] < 'a' || name[i] > 'z') {
            return false;
        }
    }
    return true;
}

static bool load_program(const char *path, Program *p, char *err, size_t err_len) {
    FILE *f = fopen(path, "r");
    if (!f) {
        snprintf(err, err_len, "failed to open: %s", path);
        return false;
    }

    memset(p, 0, sizeof(*p));
    strncpy(p->loaded_path, path, sizeof(p->loaded_path) - 1);
    char buf[512];
    int line_no = 0;

    while (fgets(buf, sizeof(buf), f)) {
        line_no++;

        char linebuf[512];
        strncpy(linebuf, buf, sizeof(linebuf) - 1);
        linebuf[sizeof(linebuf) - 1] = '\0';

        char *comment = strchr(linebuf, ';');
        if (comment) {
            *comment = '\0';
        }
        char *line = trim(linebuf);
        char first_label[LES_MAX_TOKEN];
        first_label[0] = '\0';
        if (*line == '\0') {
            continue;
        }

        while (true) {
            char *colon = strchr(line, ':');
            if (!colon) {
                break;
            }
            char label_tok[LES_MAX_TOKEN];
            size_t len = (size_t)(colon - line);
            if (len == 0 || len >= sizeof(label_tok)) {
                snprintf(err, err_len, "bad label line %d", line_no);
                fclose(f);
                return false;
            }
            memcpy(label_tok, line, len);
            label_tok[len] = '\0';
            char *label_name = trim(label_tok);
            uppercase(label_name);
            if (strlen(label_name) > LES_MAX_LABEL_NAME) {
                snprintf(err, err_len, "label too long '%s' line %d (max %d)",
                         label_name, line_no, LES_MAX_LABEL_NAME);
                fclose(f);
                return false;
            }
            if (!add_label(p, label_name, p->rom_count)) {
                snprintf(err, err_len, "duplicate label '%s' line %d", label_name, line_no);
                fclose(f);
                return false;
            }
            if (first_label[0] == '\0') {
                strncpy(first_label, label_name, sizeof(first_label) - 1);
                first_label[sizeof(first_label) - 1] = '\0';
            }
            line = trim(colon + 1);
            if (*line == '\0') {
                break;
            }
        }
        if (*line == '\0') {
            continue;
        }

        if (p->rom_count >= LES_ROM_SIZE) {
            snprintf(err, err_len, "program too large");
            fclose(f);
            return false;
        }

        char parse_copy[512];
        strncpy(parse_copy, line, sizeof(parse_copy) - 1);
        parse_copy[sizeof(parse_copy) - 1] = '\0';

        if (!parse_instruction(parse_copy, &p->rom[p->rom_count], line_no, line)) {
            snprintf(err, err_len, "parse error line %d", line_no);
            fclose(f);
            return false;
        }
        if (first_label[0] != '\0') {
            strncpy(p->rom[p->rom_count].label, first_label, LES_MAX_TOKEN - 1);
            p->rom[p->rom_count].label[LES_MAX_TOKEN - 1] = '\0';
        }
        p->rom_count++;
    }

    fclose(f);
    return true;
}

static bool get_value(CPU *cpu, const char *tok, uint8_t *value) {
    int reg = parse_register(tok);
    if (reg >= 0) {
        *value = cpu->regs[reg];
        return true;
    }
    return parse_number(tok, value);
}

static bool set_reg(CPU *cpu, const char *reg_tok, uint8_t value) {
    int reg = parse_register(reg_tok);
    if (reg < 0) {
        return false;
    }
    if (reg == REG_IU || reg == REG_ID || reg == REG_IL ||
        reg == REG_IR || reg == REG_IA || reg == REG_IB) {
        return false;
    }
    if (reg == REG_CX1 || reg == REG_CY1 || reg == REG_CX2 || reg == REG_CY2) {
        value &= 0x1f;
    }
    cpu->regs[reg] = value;
    return true;
}

static bool isc_can_execute(CPU *cpu) {
    if (cpu->isc_locked || cpu->isc >= LES_ISC_LIMIT) {
        cpu->isc_locked = true;
        return false;
    }
    return true;
}

static bool load_wram_image(uint8_t *ram, size_t ram_size) {
    FILE *f = fopen("WRAM.bin", "rb");
    if (!f) {
        return false;
    }

    memset(ram, 0, ram_size);
    (void)fread(ram, 1, ram_size, f);
    fclose(f);
    return true;
}

static bool cpu_reset(CPU *cpu) {
    memset(cpu, 0, sizeof(*cpu));
    return load_wram_image(cpu->ram, sizeof(cpu->ram));
}

static void ui_init(Ui *ui) {
    initscr();
    cbreak();
    noecho();
    keypad(stdscr, TRUE);
    curs_set(1);

    ui->asm_win = NULL;
    ui->regs_win = NULL;
    ui->screen_win = NULL;
    ui->text_win = NULL;
    ui->repl_win = NULL;
}

static void ui_layout(Ui *ui) {
    int repl_h = (LINES >= 8) ? 4 : 3;
    int top_h = LINES - repl_h;
    int text_h = (top_h >= 5) ? 3 : 1;
    int screen_h = LES_SCREEN_SIZE + 2;
    int regs_h = 10; /* 8 content rows + 2 border rows */
    int asm_h = 0;
    int right_w = LES_SCREEN_SIZE + 2;
    int left_w = 0;

    if (top_h < 4) {
        top_h = 4;
    }
    if (screen_h + text_h > top_h) {
        screen_h = top_h - text_h;
    }
    if (screen_h < 3) {
        screen_h = 3;
        text_h = top_h - screen_h;
        if (text_h < 1) {
            text_h = 1;
        }
    }

    if (right_w > COLS - 2) {
        right_w = COLS / 2;
    }
    if (right_w < 12) {
        right_w = 12;
    }

    left_w = COLS - right_w - 1;
    if (left_w < 20) {
        left_w = 20;
        right_w = COLS - left_w - 1;
        if (right_w < 12) {
            right_w = 12;
            left_w = COLS - right_w - 1;
            if (left_w < 10) {
                left_w = 10;
            }
        }
    }
    if (left_w + 1 + right_w > COLS) {
        right_w = COLS - left_w - 1;
        if (right_w < 1) {
            right_w = 1;
        }
    }

    if (regs_h > top_h - 3) {
        regs_h = top_h - 3;
    }
    if (regs_h < 3) {
        regs_h = 3;
    }
    asm_h = top_h - regs_h;
    if (asm_h < 3) {
        asm_h = 3;
        regs_h = top_h - asm_h;
        if (regs_h < 1) {
            regs_h = 1;
        }
    }

    if (ui->asm_win) delwin(ui->asm_win);
    if (ui->regs_win) delwin(ui->regs_win);
    if (ui->screen_win) delwin(ui->screen_win);
    if (ui->text_win) delwin(ui->text_win);
    if (ui->repl_win) delwin(ui->repl_win);

    ui->asm_win = newwin(asm_h, left_w, 0, 0);
    ui->regs_win = newwin(regs_h, left_w, asm_h, 0);
    ui->screen_win = newwin(screen_h, right_w, 0, left_w + 1);
    ui->text_win = newwin(text_h, right_w, screen_h, left_w + 1);
    ui->repl_win = newwin(repl_h, COLS, top_h, 0);
    keypad(ui->repl_win, TRUE);

    /* Prevent stale borders/artifacts after terminal resize relayout. */
    erase();
    refresh();
    clearok(stdscr, TRUE);
}

static void ui_shutdown(Ui *ui) {
    if (ui->asm_win) delwin(ui->asm_win);
    if (ui->regs_win) delwin(ui->regs_win);
    if (ui->screen_win) delwin(ui->screen_win);
    if (ui->text_win) delwin(ui->text_win);
    if (ui->repl_win) delwin(ui->repl_win);
    endwin();
}

static int utf8_cells(const char *s) {
    mbstate_t st;
    memset(&st, 0, sizeof(st));
    int cells = 0;
    const char *p = s;
    while (*p) {
        wchar_t wc;
        size_t n = mbrtowc(&wc, p, MB_CUR_MAX, &st);
        if (n == (size_t)-1 || n == (size_t)-2) {
            memset(&st, 0, sizeof(st));
            p++;
            cells++;
            continue;
        }
        if (n == 0) {
            break;
        }
        p += n;
        cells++;
    }
    return cells;
}

static int utf8_prefix_bytes_for_cells(const char *s, int max_cells, int *used_cells_out) {
    mbstate_t st;
    memset(&st, 0, sizeof(st));
    const char *p = s;
    const char *start = s;
    int cells = 0;
    while (*p && cells < max_cells) {
        wchar_t wc;
        size_t n = mbrtowc(&wc, p, MB_CUR_MAX, &st);
        if (n == (size_t)-1 || n == (size_t)-2) {
            memset(&st, 0, sizeof(st));
            p++;
            cells++;
            continue;
        }
        if (n == 0) {
            break;
        }
        p += n;
        cells++;
    }
    if (used_cells_out) {
        *used_cells_out = cells;
    }
    return (int)(p - start);
}

static void show_startup_logo(const char *path) {
    FILE *f = fopen(path, "r");
    char lines[LES_MAX_LOGO_LINES][LES_MAX_LOGO_COLS];
    int line_cells[LES_MAX_LOGO_LINES];
    int nlines = 0;
    int maxw = 0;
    const int extra_pad = 4;

    if (f) {
        while (nlines < LES_MAX_LOGO_LINES && fgets(lines[nlines], sizeof(lines[nlines]), f)) {
            size_t len = strlen(lines[nlines]);
            while (len > 0 && (lines[nlines][len - 1] == '\n' || lines[nlines][len - 1] == '\r')) {
                lines[nlines][--len] = '\0';
            }
            line_cells[nlines] = utf8_cells(lines[nlines]);

            if (line_cells[nlines] > maxw) {
                maxw = line_cells[nlines];
            }
            nlines++;
        }
        fclose(f);
    }

    if (nlines <= 0) {
        const char *fallback = "LES";
        strncpy(lines[0], fallback, sizeof(lines[0]) - 1);
        lines[0][sizeof(lines[0]) - 1] = '\0';
        line_cells[0] = utf8_cells(lines[0]);
        nlines = 1;
        maxw = line_cells[0];
    }

    if (!isatty(STDOUT_FILENO)) {
        return;
    }

    struct winsize ws;
    int term_rows = 24;
    int term_cols = 80;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0) {
        if (ws.ws_row > 0) term_rows = ws.ws_row;
        if (ws.ws_col > 0) term_cols = ws.ws_col;
    }

    int content_w = maxw + extra_pad;
    int content_h = nlines;
    if (content_w > term_cols - 4) {
        content_w = term_cols - 4;
    }
    if (content_h > term_rows - 4) {
        content_h = term_rows - 4;
    }
    if (content_w < 1) content_w = 1;
    if (content_h < 1) content_h = 1;

    int box_w = content_w + 2;
    int box_h = content_h + 2;
    int start_y = ((term_rows - box_h) / 2) + 1;
    int start_x = ((term_cols - box_w) / 2) + 1;
    int block_left_pad = (content_w - maxw) / 2;
    if (block_left_pad < 0) block_left_pad = 0;
    if (start_y < 1) start_y = 1;
    if (start_x < 1) start_x = 1;

    /* Clear full terminal and draw a centered ASCII box with UTF-8 content. */
    printf("\033[?25l\033[2J\033[H");
    printf("\033[%d;%dH+", start_y, start_x);
    for (int i = 0; i < content_w; i++) putchar('-');
    putchar('+');
    for (int i = 0; i < content_h; i++) {
        printf("\033[%d;%dH|", start_y + i + 1, start_x);
        int used_cells = 0;
        int draw_bytes = utf8_prefix_bytes_for_cells(lines[i], content_w - block_left_pad, &used_cells);
        int right_pad = content_w - block_left_pad - used_cells;
        if (right_pad < 0) right_pad = 0;
        for (int p = 0; p < block_left_pad; p++) {
            putchar(' ');
        }
        if (draw_bytes > 0) {
            printf("%.*s", draw_bytes, lines[i]);
        }
        for (int p = 0; p < right_pad; p++) {
            putchar(' ');
        }
        putchar('|');
    }
    printf("\033[%d;%dH+", start_y + box_h - 1, start_x);
    for (int i = 0; i < content_w; i++) putchar('-');
    putchar('+');
    fflush(stdout);

    usleep(3000000);
    printf("\033[2J\033[H\033[?25h");
    fflush(stdout);
}

static void draw_source(const Emulator *emu, Ui *ui) {
    int h = getmaxy(ui->asm_win);
    int w = getmaxx(ui->asm_win);
    int header_rows = 2;
    int body_rows = h - header_rows - 1;
    int label_w = LES_MAX_LABEL_NAME;
    int source_w = w - 16 - label_w;
    if (source_w < 0) {
        source_w = 0;
    }

    werase(ui->asm_win);
    box(ui->asm_win, 0, 0);
    mvwprintw(ui->asm_win, 0, 2, " ROM ASM ");
    mvwprintw(ui->asm_win, 1, 1, "  B  PC  LINE  %-*.*s SOURCE",
              label_w, label_w, "LABEL");

    if (!emu->loaded) {
        mvwprintw(ui->asm_win, 2, 2, "No program loaded. Use /load <file.les>");
        wrefresh(ui->asm_win);
        return;
    }

    int pc = emu->cpu.pc;
    int start = pc - body_rows / 2;
    if (start < 0) start = 0;
    if (start > emu->program.rom_count - body_rows) {
        start = emu->program.rom_count - body_rows;
        if (start < 0) start = 0;
    }

    for (int row = 0; row < body_rows; row++) {
        int idx = start + row;
        if (idx >= emu->program.rom_count) {
            break;
        }

        const Instruction *inst = &emu->program.rom[idx];
        const char *arrow = (idx == pc) ? "->" : "  ";
        char bp = emu->breakpoints[idx] ? '*' : ' ';
        const char *label = label_at_addr(&emu->program, idx);
        if (!label) {
            label = "-";
        }
        mvwprintw(ui->asm_win, row + header_rows, 1, "%s%c %03d:%4d %-*.*s %-*.*s",
                  arrow, bp, idx, inst->line_no,
                  label_w, label_w, label,
                  source_w, source_w, inst->source);
    }

    wrefresh(ui->asm_win);
}

static void draw_screen(const CPU *cpu, Ui *ui) {
    int sh = getmaxy(ui->screen_win) - 2;
    int sw = getmaxx(ui->screen_win) - 2;
    int th = getmaxy(ui->text_win);
    int tw = getmaxx(ui->text_win);

    werase(ui->screen_win);
    box(ui->screen_win, 0, 0);
    mvwprintw(ui->screen_win, 0, 2, " DISPLAY ");
    for (int y = 0; y < LES_SCREEN_SIZE && y < sh; y++) {
        for (int x = 0; x < LES_SCREEN_SIZE && x < sw; x++) {
            mvwaddch(ui->screen_win, y + 1, x + 1, cpu->display[y][x] ? (' ' | A_REVERSE) : ' ');
        }
    }
    wrefresh(ui->screen_win);

    werase(ui->text_win);
    box(ui->text_win, 0, 0);
    mvwprintw(ui->text_win, 0, 2, " TEXT ");
    if (th > 1 && tw > 2) {
        mvwprintw(ui->text_win, 1, 1, "%-*.*s", tw - 2, tw - 2, cpu->text);
    }
    wrefresh(ui->text_win);
}

static void draw_registers(const CPU *cpu, Ui *ui) {
    int h = getmaxy(ui->regs_win);
    int w = getmaxx(ui->regs_win);
    int col_w = (w - 2) / 4;

    werase(ui->regs_win);
    box(ui->regs_win, 0, 0);
    mvwprintw(ui->regs_win, 0, 2, " REGS ");

    for (int i = 0; i < REG_COUNT; i++) {
        int row = 1 + (i / 4);
        int col = 1 + (i % 4) * col_w;
        if (row >= h - 1) {
            break;
        }
        mvwprintw(ui->regs_win, row, col, "%-4s %4u",
                  reg_name((RegisterId)i), cpu->regs[i]);
    }

    int info_row = 1 + ((REG_COUNT + 3) / 4);
    if (info_row < h - 1) {
        mvwprintw(ui->regs_win, info_row, 1, "PC   %4d", cpu->pc);
        mvwprintw(ui->regs_win, info_row, 1 + col_w, "SPCN %4d", cpu->spcn);
        mvwprintw(ui->regs_win, info_row, 1 + (2 * col_w), "CMP  %4d", cpu->cmp_flag);
        mvwprintw(ui->regs_win, info_row, 1 + (3 * col_w), "HALT %4d", cpu->halted ? 1 : 0);
    }
    if (info_row + 1 < h - 1) {
        mvwprintw(ui->regs_win, info_row + 1, 1, "SPC1 %4d", cpu->spc[0]);
        mvwprintw(ui->regs_win, info_row + 1, 1 + col_w, "SPC2 %4d", cpu->spc[1]);
        mvwprintw(ui->regs_win, info_row + 1, 1 + (2 * col_w), "SPC3 %4d", cpu->spc[2]);
        mvwprintw(ui->regs_win, info_row + 1, 1 + (3 * col_w), "SPC4 %4d", cpu->spc[3]);
    }
    if (info_row + 2 < h - 1) {
        mvwprintw(ui->regs_win, info_row + 2, 1, "ISC %llu",
                  (unsigned long long)cpu->isc);
    }

    wrefresh(ui->regs_win);
}

static void draw_repl(const Emulator *emu, Ui *ui, const char *input) {
    int rw = getmaxx(ui->repl_win);
    int rh = getmaxy(ui->repl_win);
    int prompt_col = 2;
    int status_w = rw - 2;
    int input_w = rw - (prompt_col + 2) - 1;

    if (status_w < 0) status_w = 0;
    if (input_w < 0) input_w = 0;

    werase(ui->repl_win);
    box(ui->repl_win, 0, 0);
    mvwprintw(ui->repl_win, 0, 2, " DEBUG REPL ");
    if (rh > 1) {
        mvwprintw(ui->repl_win, 1, 1, "%-*.*s", status_w, status_w, emu->status);
    }
    if (rh > 2) {
        mvwprintw(ui->repl_win, 2, prompt_col, "> %-*.*s", input_w, input_w, input);
        wmove(ui->repl_win, 2, prompt_col + 2 + (int)strlen(input));
    }
    wrefresh(ui->repl_win);
}

static void ui_render(const Emulator *emu, Ui *ui, const char *input) {
    draw_source(emu, ui);
    draw_registers(&emu->cpu, ui);
    draw_screen(&emu->cpu, ui);
    draw_repl(emu, ui, input);
}

static void ui_render_runtime(const Emulator *emu, Ui *ui, const char *input,
                              bool sample_debug, bool sample_frame) {
    if (!sample_frame) {
        return;
    }
    if (sample_debug) {
        draw_source(emu, ui);
        draw_registers(&emu->cpu, ui);
    }
    draw_screen(&emu->cpu, ui);
    draw_repl(emu, ui, input);
}

static long long now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + (long long)ts.tv_nsec / 1000000LL;
}

static bool execute_one(CPU *cpu, const Program *p) {
    if (cpu->pc >= p->rom_count) {
        cpu->halted = true;
        return false;
    }

    Instruction inst = p->rom[cpu->pc];
    bool jumped = false;
    bool isc_cleared = false;
    uint8_t a = 0;
    uint8_t b = 0;
    uint8_t c = 0;
    int target = -1;

    switch (inst.op) {
    case OP_SET:
        if (inst.argc != 2) return false;
        if (parse_register(inst.args[0]) >= 0) {
            if (!get_value(cpu, inst.args[1], &a) || !set_reg(cpu, inst.args[0], a)) return false;
        } else if (parse_register(inst.args[1]) >= 0) {
            if (!get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[1], a)) return false;
        } else {
            return false;
        }
        break;
    case OP_DUPE:
        if (inst.argc != 2 || !get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[1], a)) return false;
        break;
    case OP_LOAD:
        if (inst.argc != 1 || !set_reg(cpu, inst.args[0], cpu->ram[cpu->regs[REG_MR]])) return false;
        break;
    case OP_STORE:
        if (inst.argc != 1 || !get_value(cpu, inst.args[0], &a)) return false;
        cpu->ram[cpu->regs[REG_MW]] = a;
        break;
    case OP_ADD:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a + b))) return false;
        break;
    case OP_SUB:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a - b))) return false;
        break;
    case OP_INC:
        if (inst.argc == 1) {
            if (!get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[0], (uint8_t)(a + 1))) return false;
        } else if (inst.argc == 2) {
            if (!get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[1], (uint8_t)(a + 1))) return false;
        } else {
            return false;
        }
        break;
    case OP_DEC:
        if (inst.argc == 1) {
            if (!get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[0], (uint8_t)(a - 1))) return false;
        } else if (inst.argc == 2) {
            if (!get_value(cpu, inst.args[0], &a) || !set_reg(cpu, inst.args[1], (uint8_t)(a - 1))) return false;
        } else {
            return false;
        }
        break;
    case OP_CMP:
        if (inst.argc != 2 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b)) return false;
        cpu->cmp_flag = (a > b) - (a < b);
        break;
    case OP_RND:
        if (inst.argc != 1 || !set_reg(cpu, inst.args[0], (uint8_t)(rand() & 0xff))) return false;
        break;
    case OP_SHIFTL:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a << (b & 7)))) return false;
        break;
    case OP_SHIFTR:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a >> (b & 7)))) return false;
        break;
    case OP_AND:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a & b))) return false;
        break;
    case OP_OR:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a | b))) return false;
        break;
    case OP_XOR:
        if (inst.argc != 3 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b) ||
            !set_reg(cpu, inst.args[2], (uint8_t)(a ^ b))) return false;
        break;
    case OP_JMP:
        if (inst.argc != 1) return false;
        if (!resolve_label_ref(p, inst.args[0], &target)) return false;
        cpu->pc = target;
        jumped = true;
        break;
    case OP_JMPE:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag == 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_JMPNE:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag != 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_JMPGT:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag > 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_JMPLT:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag < 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_JMPGE:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag >= 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_JMPLE:
        if (inst.argc != 1) return false;
        if (cpu->cmp_flag <= 0) {
            if (!resolve_label_ref(p, inst.args[0], &target)) return false;
            cpu->pc = target;
            jumped = true;
        }
        break;
    case OP_CALL:
        if (inst.argc != 1) return false;
        if (!resolve_label_ref(p, inst.args[0], &target)) return false;
        if (cpu->spcn < 0 || cpu->spcn >= 4) return false;
        cpu->spc[cpu->spcn] = cpu->pc + 1;
        cpu->spcn++;
        cpu->pc = target;
        jumped = true;
        break;
    case OP_RET:
        if (inst.argc != 0) return false;
        if (cpu->spcn <= 0 || cpu->spcn > 4) return false;
        cpu->spcn--;
        cpu->pc = cpu->spc[cpu->spcn];
        jumped = true;
        break;
    case OP_INIT:
        if (inst.argc != 0) return false;
        /* INIT clears machine state but remains a normal executable instruction. */
        int old_pc = cpu->pc;
        srand(1);
        memset(cpu->regs, 0, sizeof(cpu->regs));
        if (!load_wram_image(cpu->ram, sizeof(cpu->ram))) return false;
        memset(cpu->vram, 0, sizeof(cpu->vram));
        memset(cpu->display, 0, sizeof(cpu->display));
        memset(cpu->text, 0, sizeof(cpu->text));
        cpu->cmp_flag = 0;
        memset(cpu->spc, 0, sizeof(cpu->spc));
        cpu->spcn = 0;
        cpu->isc = 0;
        cpu->isc_locked = false;
        isc_cleared = true;
        cpu->halted = false;
        cpu->pc = old_pc;
        break;
    case OP_HALT:
        if (inst.argc != 0) return false;
        cpu->halted = true;
        break;
    case OP_INPUT:
        if (inst.argc != 0) return false;
        cpu->regs[REG_IU] = 0;
        cpu->regs[REG_ID] = 0;
        cpu->regs[REG_IL] = 0;
        cpu->regs[REG_IR] = 0;
        cpu->regs[REG_IA] = 0;
        cpu->regs[REG_IB] = 0;
        if (!g_in_run_mode) {
            wtimeout(stdscr, 0);
        }
        if (g_forward_key != ERR) {
            if (g_in_run_mode && (g_forward_key == 'b' || g_forward_key == 'B')) {
                g_async_break_requested = true;
            } else {
                apply_input_key(cpu, g_forward_key);
            }
            g_forward_key = ERR;
        }
        while (true) {
            int key = getch();
            if (key == ERR) {
                break;
            }
            if (g_in_run_mode && (key == 'b' || key == 'B')) {
                g_async_break_requested = true;
                break;
            }
            apply_input_key(cpu, key);
        }
        if (!g_in_run_mode) {
            wtimeout(stdscr, -1);
        }
        break;
    case OP_PRINT:
        if (inst.argc != 0) return false;
        memset(cpu->text, 0, sizeof(cpu->text));
        for (int i = 0; i < LES_TEXT_SIZE; i++) {
            c = cpu->ram[(uint8_t)(cpu->regs[REG_MR] + i)];
            if (!c) {
                break;
            }
            cpu->text[i] = (char)c;
        }
        break;
    case OP_GETP:
        if (inst.argc != 2 || !get_value(cpu, inst.args[0], &a)) return false;
        if (a == 1) {
            b = cpu->display[cpu->regs[REG_CY1] & 31][cpu->regs[REG_CX1] & 31];
        } else if (a == 2) {
            b = cpu->display[cpu->regs[REG_CY2] & 31][cpu->regs[REG_CX2] & 31];
        } else {
            return false;
        }
        if (!set_reg(cpu, inst.args[1], b)) return false;
        break;
    case OP_SETP:
        if (inst.argc != 2 || !get_value(cpu, inst.args[0], &a) || !get_value(cpu, inst.args[1], &b)) return false;
        if (a == 1) {
            cpu->vram[cpu->regs[REG_CY1] & 31][cpu->regs[REG_CX1] & 31] = (uint8_t)(b & 1);
        } else if (a == 2) {
            cpu->vram[cpu->regs[REG_CY2] & 31][cpu->regs[REG_CX2] & 31] = (uint8_t)(b & 1);
        } else {
            return false;
        }
        break;
    case OP_CLEAR:
        if (inst.argc != 0) return false;
        memset(cpu->vram, 0, sizeof(cpu->vram));
        break;
    case OP_DRAW:
        if (inst.argc != 0) return false;
        memcpy(cpu->display, cpu->vram, sizeof(cpu->display));
        break;
    case OP_SLEEP:
        if (inst.argc != 1) return false;
        {
            long sleep_ms = 0;
            int sleep_reg = parse_register(inst.args[0]);
            if (sleep_reg >= 0) {
                sleep_ms = cpu->regs[sleep_reg];
            } else if (!parse_number_long(inst.args[0], &sleep_ms)) {
                return false;
            }
            if (sleep_ms < 0) {
                sleep_ms = 0;
            }
            while (sleep_ms > 0) {
                long chunk_ms = (sleep_ms > 50) ? 50 : sleep_ms;
                usleep((useconds_t)chunk_ms * 1000);
                sleep_ms -= chunk_ms;

                /* Keep long sleeps responsive to debugger break key. */
                if (g_in_run_mode) {
                    int key = getch();
                    if (key == 'b' || key == 'B') {
                        g_async_break_requested = true;
                        break;
                    }
                    if (key != ERR) {
                        ungetch(key);
                    }
                }
            }
        }
        break;
    case OP_TRAP:
        if (inst.argc != 0) return false;
        if (g_traps_enabled) {
            g_trap_requested = true;
        }
        break;
    case OP_INVALID:
        return false;
    }

    if (!jumped && !cpu->halted) {
        cpu->pc++;
    }
    if (!isc_cleared) {
        cpu->isc++;
        if (cpu->isc >= LES_ISC_LIMIT) {
            cpu->isc_locked = true;
            cpu->halted = true;
        }
    }
    return true;
}

static bool run_until_break(Emulator *emu, Ui *ui, int max_steps, bool skip_initial_breakpoint) {
    int steps = 0;
    const char *run_input = "/run (press b to break)";
    long long last_debug_sample_ms = 0;
    bool first_cycle = true;

    nodelay(stdscr, TRUE);
    g_in_run_mode = true;
    g_async_break_requested = false;
    g_trap_requested = false;
    g_forward_key = ERR;

    while (!emu->cpu.halted) {
        long long now = now_ms();
        bool sample_debug = (last_debug_sample_ms == 0 || now - last_debug_sample_ms >= 1000);
        if (sample_debug) {
            last_debug_sample_ms = now;
        }

        int ch = getch();
        if (ch == KEY_RESIZE) {
            resizeterm(0, 0);
            ui_layout(ui);
            erase();
            refresh();
            ui_render(emu, ui, run_input);
            continue;
        }
        if (ch == 'b' || ch == 'B') {
            snprintf(emu->status, sizeof(emu->status), "manual break at %d", emu->cpu.pc);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }
        if (ch != ERR) {
            if (g_forward_key == ERR) {
                g_forward_key = ch;
            }
        }

        if (emu->cpu.pc >= emu->program.rom_count) {
            snprintf(emu->status, sizeof(emu->status), "pc out of range: %d", emu->cpu.pc);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return false;
        }
        if (!isc_can_execute(&emu->cpu)) {
            snprintf(emu->status, sizeof(emu->status),
                     "isc limit reached (%llu), run /reset",
                     (unsigned long long)LES_ISC_LIMIT);
            emu->cpu.halted = true;
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }
        if (emu->breakpoints[emu->cpu.pc] &&
            !(skip_initial_breakpoint && first_cycle)) {
            snprintf(emu->status, sizeof(emu->status), "breakpoint hit at %d", emu->cpu.pc);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }
        int pc_before = emu->cpu.pc;
        if (!execute_one(&emu->cpu, &emu->program)) {
            snprintf(emu->status, sizeof(emu->status), "execution error at pc %d", emu->cpu.pc);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return false;
        }
        if (g_trap_requested) {
            snprintf(emu->status, sizeof(emu->status), "trap hit at %d", emu->cpu.pc - 1);
            g_trap_requested = false;
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }
        if (g_async_break_requested) {
            snprintf(emu->status, sizeof(emu->status), "manual break at %d", emu->cpu.pc);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }

        ui_render_runtime(emu, ui, run_input, sample_debug,
                          sample_debug || emu->program.rom[pc_before].op == OP_DRAW);
        first_cycle = false;
        steps++;
        if (max_steps > 0 && steps >= max_steps) {
            snprintf(emu->status, sizeof(emu->status), "stepped %d instruction", steps);
            g_in_run_mode = false;
            nodelay(stdscr, FALSE);
            return true;
        }
    }

    snprintf(emu->status, sizeof(emu->status), "program halted");
    g_in_run_mode = false;
    nodelay(stdscr, FALSE);
    return true;
}

static void clear_breakpoints(Emulator *emu) {
    memset(emu->breakpoints, 0, sizeof(emu->breakpoints));
}

static void process_command(Emulator *emu, Ui *ui, const char *cmdline, bool *quit) {
    char work[LES_MAX_LINE];
    bool reused_last = false;
    strncpy(work, cmdline, sizeof(work) - 1);
    work[sizeof(work) - 1] = '\0';

    char *cmd = trim(work);
    if (*cmd == '\0') {
        if (emu->last_cmd[0] == '\0') {
            return;
        }
        strncpy(work, emu->last_cmd, sizeof(work) - 1);
        work[sizeof(work) - 1] = '\0';
        cmd = trim(work);
        reused_last = true;
    }
    if (*cmd == '\0') {
        return;
    }

    if (!reused_last) {
        strncpy(emu->last_cmd, cmd, sizeof(emu->last_cmd) - 1);
        emu->last_cmd[sizeof(emu->last_cmd) - 1] = '\0';
    }

    char *verb = strtok(cmd, " \t");
    if (!verb) {
        return;
    }

    if (strcmp(verb, "/quit") == 0 || strcmp(verb, "/q") == 0) {
        *quit = true;
        return;
    }

    if (strcmp(verb, "/help") == 0) {
        snprintf(emu->status, sizeof(emu->status),
                 "/load <file> /run(/press b) /step /break <pc|label> /clearbreak /toggletraps /reset /quit");
        return;
    }

    if (strcmp(verb, "/load") == 0) {
        char *rom_name = strtok(NULL, "");
        if (!rom_name) {
            snprintf(emu->status, sizeof(emu->status), "rom name error");
            return;
        }
        rom_name = trim(rom_name);
        if (!valid_rom_name(rom_name)) {
            snprintf(emu->status, sizeof(emu->status), "rom name error");
            return;
        }

        char rom_path[LES_MAX_LINE];
        int n = snprintf(rom_path, sizeof(rom_path), "%s/%s", LES_ROM_DIR, rom_name);
        if (n < 0 || n >= (int)sizeof(rom_path)) {
            snprintf(emu->status, sizeof(emu->status), "rom name error");
            return;
        }

        char err[LES_MAX_LINE];
        Program p;
        if (!load_program(rom_path, &p, err, sizeof(err))) {
            snprintf(emu->status, sizeof(emu->status), "load failed: %.220s", err);
            return;
        }

        emu->program = p;
        emu->loaded = true;
        snprintf(emu->status, sizeof(emu->status),
                 "loaded %s (%d instructions)", rom_name, p.rom_count);
        return;
    }

    if (!emu->loaded) {
        snprintf(emu->status, sizeof(emu->status), "no program loaded; use /load <file.les>");
        return;
    }

    if (strcmp(verb, "/break") == 0) {
        char *arg = strtok(NULL, " \t");
        long pc = 0;
        char label[LES_MAX_TOKEN];
        int target = -1;

        if (!arg) {
            snprintf(emu->status, sizeof(emu->status), "usage: /break <pc|label>");
            return;
        }
        if (parse_number_long(arg, &pc)) {
            if (pc < 0 || pc >= emu->program.rom_count) {
                snprintf(emu->status, sizeof(emu->status), "usage: /break <pc 0-%d>", emu->program.rom_count - 1);
                return;
            }
            emu->breakpoints[pc] = true;
            snprintf(emu->status, sizeof(emu->status), "breakpoint set at %ld", pc);
            return;
        }
        if (!normalize_label_token(arg, label, sizeof(label))) {
            snprintf(emu->status, sizeof(emu->status), "usage: /break <pc|label>");
            return;
        }
        target = label_lookup(&emu->program, label);
        if (target < 0 || target >= emu->program.rom_count) {
            snprintf(emu->status, sizeof(emu->status), "unknown label: %s", label);
            return;
        }
        emu->breakpoints[target] = true;
        snprintf(emu->status, sizeof(emu->status), "breakpoint set at %d (%s)", target, label);
        return;
    }

    if (strcmp(verb, "/clearbreak") == 0) {
        char *arg = strtok(NULL, " \t");
        if (!arg) {
            clear_breakpoints(emu);
            snprintf(emu->status, sizeof(emu->status), "all breakpoints cleared");
            return;
        }
        long pc = 0;
        char label[LES_MAX_TOKEN];
        int target = -1;

        if (parse_number_long(arg, &pc)) {
            if (pc < 0 || pc >= emu->program.rom_count) {
                snprintf(emu->status, sizeof(emu->status), "usage: /clearbreak [pc|label]");
                return;
            }
            emu->breakpoints[pc] = false;
            snprintf(emu->status, sizeof(emu->status), "breakpoint cleared at %ld", pc);
            return;
        }

        if (!normalize_label_token(arg, label, sizeof(label))) {
            snprintf(emu->status, sizeof(emu->status), "usage: /clearbreak [pc|label]");
            return;
        }
        target = label_lookup(&emu->program, label);
        if (target < 0 || target >= emu->program.rom_count) {
            snprintf(emu->status, sizeof(emu->status), "unknown label: %s", label);
            return;
        }
        emu->breakpoints[target] = false;
        snprintf(emu->status, sizeof(emu->status), "breakpoint cleared at %d (%s)", target, label);
        return;
    }

    if (strcmp(verb, "/step") == 0) {
        if (!isc_can_execute(&emu->cpu)) {
            snprintf(emu->status, sizeof(emu->status),
                     "isc limit reached (%llu), run /reset",
                     (unsigned long long)LES_ISC_LIMIT);
            return;
        }
        if (emu->cpu.halted) {
            snprintf(emu->status, sizeof(emu->status), "program already halted");
            return;
        }
        if (emu->cpu.pc >= emu->program.rom_count) {
            snprintf(emu->status, sizeof(emu->status), "pc out of range");
            return;
        }
        if (!execute_one(&emu->cpu, &emu->program)) {
            snprintf(emu->status, sizeof(emu->status), "execution error at pc %d", emu->cpu.pc);
            return;
        }
        snprintf(emu->status, sizeof(emu->status), "stepped to pc %d", emu->cpu.pc);
        return;
    }

    if (strcmp(verb, "/run") == 0) {
        if (!isc_can_execute(&emu->cpu)) {
            snprintf(emu->status, sizeof(emu->status),
                     "isc limit reached (%llu), run /reset",
                     (unsigned long long)LES_ISC_LIMIT);
            return;
        }
        emu->cpu.pc = 0;
        emu->cpu.halted = false;
        (void)run_until_break(emu, ui, 0, true);
        return;
    }

    if (strcmp(verb, "/continue") == 0) {
        if (!isc_can_execute(&emu->cpu)) {
            snprintf(emu->status, sizeof(emu->status),
                     "isc limit reached (%llu), run /reset",
                     (unsigned long long)LES_ISC_LIMIT);
            return;
        }
        (void)run_until_break(emu, ui, 0, true);
        return;
    }

    if (strcmp(verb, "/reset") == 0) {
        srand(1);
        bool ok = cpu_reset(&emu->cpu);
        snprintf(emu->status, sizeof(emu->status),
                 ok ? "cpu reset; pc=%d (WRAM.bin loaded)" : "cpu reset; pc=%d (WRAM.bin missing)",
                 emu->cpu.pc);
        return;
    }

    if (strcmp(verb, "/toggletraps") == 0) {
        g_traps_enabled = !g_traps_enabled;
        snprintf(emu->status, sizeof(emu->status),
                 "traps %s", g_traps_enabled ? "enabled" : "disabled");
        return;
    }

    snprintf(emu->status, sizeof(emu->status), "unknown command: %s", verb);
}

static void read_repl_line(Emulator *emu, Ui *ui, char *input, size_t input_len) {
    size_t len = 0;
    int ch = 0;

    input[0] = '\0';
    while (true) {
        ui_render(emu, ui, input);
        ch = wgetch(ui->repl_win);
        if (ch == KEY_RESIZE) {
            resizeterm(0, 0);
            ui_layout(ui);
            erase();
            refresh();
            continue;
        }
        if (ch == '\n' || ch == '\r' || ch == KEY_ENTER) {
            input[len] = '\0';
            return;
        }
        if (ch == KEY_BACKSPACE || ch == 127 || ch == '\b') {
            if (len > 0) {
                len--;
                input[len] = '\0';
            }
            continue;
        }
        if (isprint(ch) && len + 1 < input_len) {
            input[len++] = (char)ch;
            input[len] = '\0';
        }
    }
}

int main(void) {
    Emulator emu;
    Ui ui;
    bool quit = false;
    char input[LES_MAX_LINE];
    bool wram_ok = false;

    memset(&emu, 0, sizeof(emu));
    (void)setlocale(LC_ALL, "");
    srand(1);
    wram_ok = cpu_reset(&emu.cpu);
    snprintf(emu.status, sizeof(emu.status),
             wram_ok ? "startup reset complete (WRAM.bin loaded). use /load <file.les>"
                     : "startup reset complete (WRAM.bin missing). use /load <file.les>");

    show_startup_logo("les_logo.txt");
    ui_init(&ui);
    ui_layout(&ui);

    while (!quit) {
        curs_set(1);
        read_repl_line(&emu, &ui, input, LES_MAX_LINE);

        process_command(&emu, &ui, input, &quit);
    }

    ui_shutdown(&ui);
    return 0;
}
