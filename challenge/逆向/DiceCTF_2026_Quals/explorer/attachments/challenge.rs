// SPDX-License-Identifier: GPL-2.0

//! Rust misc-device CTF challenge: seeded maze game over ioctls.
//!
//! Ioctls:
//! - GET_SEED    -> u32
//! - GET_X       -> u32 (maze X dimension)
//! - GET_Y       -> u32 (maze Y dimension)
//! - GET_Z       -> u32 (maze Z dimension)
//! - GET_STEPS   -> u32
//! - GET_STATE   -> u32 (0=Playing, 1=Won, 2=Lost)
//! - GET_EXITS   -> u32 bitmask (bit0=N, bit1=E, bit2=S, bit3=W, bit4=U, bit5=D)
//! - GET_FLAG    -> [u8; 64] (valid only when Won)
//! - MOVE        <- u32 direction (0=N, 1=E, 2=S, 3=W, 4=U, 5=D)
//! - RESET       (no arg)
//!
//! The maze is generated from a per-open seed. Each node is an `Arc` object.

use core::pin::Pin;

use kernel::{
    bindings,
    c_str,
    cpu::CpuId,
    fs::File,
    ioctl::{_IO, _IOR, _IOW, _IOC_SIZE},
    miscdevice::{MiscDevice, MiscDeviceOptions, MiscDeviceRegistration},
    new_mutex,
    prelude::*,
    sync::{Arc, Mutex},
    uaccess::UserSlice,
};

const MAZE_DIM_MIN: usize = 8;
const MAZE_DIM_MAX: usize = 16;
const CHAL_FLAG_LEN: usize = 64;
const FLAG_VALUE: &[u8] = b"dice{twisty_rusty_kernel_maze}\0";

const NORTH: usize = 0;
const EAST: usize = 1;
const SOUTH: usize = 2;
const WEST: usize = 3;
const UP: usize = 4;
const DOWN: usize = 5;

const IOCTL_MAGIC: u32 = b"dice"[0] as u32;
const CHAL_GET_SEED: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x80);
const CHAL_GET_X: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x81);
const CHAL_GET_Y: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x82);
const CHAL_GET_Z: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x83);
const CHAL_GET_STEPS: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x84);
const CHAL_GET_STATE: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x85);
const CHAL_GET_EXITS: u32 = _IOR::<u32>(IOCTL_MAGIC, 0x86);
const CHAL_GET_FLAG: u32 = _IOR::<[u8; CHAL_FLAG_LEN]>(IOCTL_MAGIC, 0x87);
const CHAL_MOVE: u32 = _IOW::<u32>(IOCTL_MAGIC, 0x88);
const CHAL_RESET: u32 = _IO(IOCTL_MAGIC, 0x89);

module! {
    type: ChallengeModule,
    name: "challenge",
    authors: ["DiceCTF"],
    description: "seeded maze challenge over ioctls",
    license: "GPL",
}

#[pin_data]
struct ChallengeModule {
    #[pin]
    #[allow(dead_code)]
    miscdev: MiscDeviceRegistration<ChallengeDevice>,
}

impl kernel::InPlaceModule for ChallengeModule {
    fn init(_module: &'static ThisModule) -> impl PinInit<Self, Error> {
        let opts = MiscDeviceOptions {
            name: c_str!("challenge"),
        };

        try_pin_init!(Self {
            miscdev <- MiscDeviceRegistration::register(opts),
        })
    }
}

struct MazeNodeInner {
    exits: [Option<Arc<MazeNode>>; 6],
}

impl MazeNodeInner {
    fn new() -> Self {
        Self {
            exits: [None, None, None, None, None, None],
        }
    }
}

#[pin_data]
struct MazeNode {
    id: usize,
    kind: NodeType,
    #[pin]
    inner: Mutex<MazeNodeInner>,
}

#[derive(Copy, Clone, PartialEq, Eq)]
enum NodeType {
    None,
    Goal,
    Spikes,
}

#[derive(Copy, Clone, PartialEq, Eq)]
enum GameState {
    Playing,
    Won,
    Lost,
}

impl GameState {
    const fn as_u32(self) -> u32 {
        match self {
            GameState::Playing => 0,
            GameState::Won => 1,
            GameState::Lost => 2,
        }
    }
}

struct MazeGame {
    seed: u32,
    sx: usize,
    sy: usize,
    sz: usize,
    pos: Arc<MazeNode>,
    steps: u32,
    state: GameState,
    nodes: KVVec<Arc<MazeNode>>,
}

impl Drop for MazeGame {
    fn drop(&mut self) {
        // Break Arc cycles formed by bidirectional maze edges.
        for node in &self.nodes {
            let mut inner = node.inner.lock();
            inner.exits = [None, None, None, None, None, None];
        }
    }
}

#[pin_data]
struct ChallengeDevice {
    #[pin]
    game: Mutex<MazeGame>,
}

#[vtable]
impl MiscDevice for ChallengeDevice {
    type Ptr = Pin<KBox<Self>>;

    fn open(_file: &File, _misc: &MiscDeviceRegistration<Self>) -> Result<Self::Ptr> {
        let seed = fresh_seed();
        let mut rng = seed ^ 0xA53C_91E7;
        let sx = random_dim(&mut rng);
        let sy = random_dim(&mut rng);
        let sz = random_dim(&mut rng);
        let game = MazeGame::new(seed, sx, sy, sz)?;

        KBox::try_pin_init(
            try_pin_init!(Self {
                game <- new_mutex!(game),
            }),
            GFP_KERNEL,
        )
    }

    fn ioctl(me: Pin<&ChallengeDevice>, _file: &File, cmd: u32, arg: usize) -> Result<isize> {
        let arg = UserPtr::from_addr(arg);
        let size = _IOC_SIZE(cmd);

        match cmd {
            CHAL_GET_SEED => {
                let game = me.game.lock();
                UserSlice::new(arg, size).writer().write(&game.seed)?;
            }
            CHAL_GET_X => {
                let game = me.game.lock();
                let x = game.sx as u32;
                UserSlice::new(arg, size).writer().write(&x)?;
            }
            CHAL_GET_Y => {
                let game = me.game.lock();
                let y = game.sy as u32;
                UserSlice::new(arg, size).writer().write(&y)?;
            }
            CHAL_GET_Z => {
                let game = me.game.lock();
                let z = game.sz as u32;
                UserSlice::new(arg, size).writer().write(&z)?;
            }
            CHAL_GET_STEPS => {
                let game = me.game.lock();
                UserSlice::new(arg, size).writer().write(&game.steps)?;
            }
            CHAL_GET_STATE => {
                let game = me.game.lock();
                let state = game.state.as_u32();
                UserSlice::new(arg, size).writer().write(&state)?;
            }
            CHAL_GET_EXITS => {
                let game = me.game.lock();
                let mask = exits_mask(&game.pos);
                UserSlice::new(arg, size).writer().write(&mask)?;
            }
            CHAL_GET_FLAG => {
                let game = me.game.lock();
                if game.state != GameState::Won {
                    return Err(EPERM);
                }
                let flag = build_flag();
                UserSlice::new(arg, size).writer().write_slice(&flag)?;
            }
            CHAL_MOVE => {
                let dir = UserSlice::new(arg, size).reader().read::<u32>()?;
                let Some(dir) = parse_dir(dir) else {
                    return Err(EINVAL);
                };

                let mut game = me.game.lock();
                handle_move(&mut game, dir)?;
            }
            CHAL_RESET => {
                let mut game = me.game.lock();
                game.pos = game.nodes[0].clone();
                game.steps = 0;
                game.state = GameState::Playing;
            }
            _ => return Err(ENOTTY),
        }

        Ok(0)
    }
}

impl MazeGame {
    fn new(seed: u32, sx: usize, sy: usize, sz: usize) -> Result<Self> {
        let nodes = generate_maze(seed, sx, sy, sz)?;

        Ok(Self {
            seed,
            sx,
            sy,
            sz,
            pos: nodes[0].clone(),
            steps: 0,
            state: GameState::Playing,
            nodes,
        })
    }
}

fn make_node(id: usize, kind: NodeType) -> Result<Arc<MazeNode>> {
    Arc::pin_init(
        try_pin_init!(MazeNode {
            id,
            kind,
            inner <- new_mutex!(MazeNodeInner::new()),
        }),
        GFP_KERNEL,
    )
}

fn link_bidirectional(a: &Arc<MazeNode>, b: &Arc<MazeNode>, d_from_a: usize) {
    {
        let mut ai = a.inner.lock();
        ai.exits[d_from_a] = Some(b.clone());
    }

    {
        let mut bi = b.inner.lock();
        bi.exits[opposite(d_from_a)] = Some(a.clone());
    }
}

fn generate_maze(seed: u32, sx: usize, sy: usize, sz: usize) -> Result<KVVec<Arc<MazeNode>>> {
    let count = sx * sy * sz;
    let goal = count - 1;
    let exits = carve_maze(seed, sx, sy, sz)?;
    let on_path = find_goal_path(&exits, sx, sy, sz)?;
    let kinds = node_types(seed, &exits, &on_path, goal)?;

    let mut nodes = KVVec::with_capacity(count, GFP_KERNEL)?;
    for id in 0..count {
        nodes.push(make_node(id, kinds[id])?, GFP_KERNEL)?;
    }
    for id in 0..count {
        for d in 0..6 {
            if exits[id] & (1u8 << d) == 0 {
                continue;
            }
            let Some(to) = neighbor(id, d, sx, sy, sz) else {
                continue;
            };
            if to > id {
                link_bidirectional(&nodes[id], &nodes[to], d);
            }
        }
    }

    Ok(nodes)
}

fn carve_maze(seed: u32, sx: usize, sy: usize, sz: usize) -> Result<KVVec<u8>> {
    let count = sx * sy * sz;
    let mut exits = KVVec::with_capacity(count, GFP_KERNEL)?;
    let mut visited = KVVec::with_capacity(count, GFP_KERNEL)?;
    let mut stack = KVVec::with_capacity(count, GFP_KERNEL)?;

    for _ in 0..count {
        exits.push(0u8, GFP_KERNEL)?;
        visited.push(0u8, GFP_KERNEL)?;
    }

    let mut rng = seed ^ 0x9E37_79B9;
    visited[0] = 1;
    stack.push(0usize, GFP_KERNEL)?;

    while let Some(&cur) = stack.last() {
        let mut nidx = [0usize; 6];
        let mut ndir = [0usize; 6];
        let mut n = 0usize;

        for d in 0..6 {
            let Some(ni) = neighbor(cur, d, sx, sy, sz) else {
                continue;
            };
            if visited[ni] == 0 {
                nidx[n] = ni;
                ndir[n] = d;
                n += 1;
            }
        }

        if n == 0 {
            stack.pop();
            continue;
        }

        let pick = (next_rand(&mut rng) as usize) % n;
        let to = nidx[pick];
        let d = ndir[pick];

        exits[cur] |= 1u8 << d;
        exits[to] |= 1u8 << opposite(d);

        visited[to] = 1;
        stack.push(to, GFP_KERNEL)?;
    }

    Ok(exits)
}

fn find_goal_path(exits: &[u8], sx: usize, sy: usize, sz: usize) -> Result<KVVec<u8>> {
    let count = sx * sy * sz;
    let goal = count - 1;
    let mut parent = KVVec::with_capacity(count, GFP_KERNEL)?;
    let mut vis = KVVec::with_capacity(count, GFP_KERNEL)?;
    let mut queue = KVVec::with_capacity(count, GFP_KERNEL)?;
    let mut on_path = KVVec::with_capacity(count, GFP_KERNEL)?;

    for _ in 0..count {
        parent.push(usize::MAX, GFP_KERNEL)?;
        vis.push(0u8, GFP_KERNEL)?;
        on_path.push(0u8, GFP_KERNEL)?;
    }

    vis[0] = 1;
    queue.push(0usize, GFP_KERNEL)?;

    let mut head = 0usize;
    while head < queue.len() {
        let cur = queue[head];
        head += 1;
        if cur == goal {
            break;
        }

        for d in 0..6 {
            if exits[cur] & (1u8 << d) == 0 {
                continue;
            }
            let Some(to) = neighbor(cur, d, sx, sy, sz) else {
                continue;
            };
            if vis[to] != 0 {
                continue;
            }

            vis[to] = 1;
            parent[to] = cur;
            queue.push(to, GFP_KERNEL)?;
        }
    }

    let mut cur = goal;
    while cur != usize::MAX {
        on_path[cur] = 1;
        if cur == 0 {
            break;
        }
        cur = parent[cur];
    }

    Ok(on_path)
}

fn exits_mask(node: &Arc<MazeNode>) -> u32 {
    let inner = node.inner.lock();
    let mut mask = 0u32;
    if inner.exits[NORTH].is_some() {
        mask |= 1u32 << NORTH;
    }
    if inner.exits[EAST].is_some() {
        mask |= 1u32 << EAST;
    }
    if inner.exits[SOUTH].is_some() {
        mask |= 1u32 << SOUTH;
    }
    if inner.exits[WEST].is_some() {
        mask |= 1u32 << WEST;
    }
    if inner.exits[UP].is_some() {
        mask |= 1u32 << UP;
    }
    if inner.exits[DOWN].is_some() {
        mask |= 1u32 << DOWN;
    }
    mask
}

fn handle_move(game: &mut MazeGame, dir: usize) -> Result {
    match game.state {
        GameState::Won | GameState::Lost => return Err(EPERM),
        GameState::Playing => {}
    }

    let next = {
        let inner = game.pos.inner.lock();
        inner.exits[dir].clone()
    };

    let Some(next_node) = next else {
        return Err(EAGAIN);
    };

    game.pos = next_node;
    game.steps = game.steps.wrapping_add(1);

    match game.pos.kind {
        NodeType::Goal => game.state = GameState::Won,
        NodeType::Spikes => game.state = GameState::Lost,
        NodeType::None => {}
    }

    Ok(())
}

fn fresh_seed() -> u32 {
    // SAFETY: `jiffies` is a valid kernel global.
    let ticks = unsafe { bindings::jiffies } as u64;
    let cpu = u32::from(CpuId::current());
    (ticks as u32)
        .wrapping_mul(0x45d9f3b)
        .rotate_left(5)
        ^ cpu.wrapping_mul(0x9E37_79B9)
        ^ 0xC7F0_A5E1
}

fn next_rand(seed: &mut u32) -> u32 {
    let mut x = *seed;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *seed = x;
    x
}

fn random_dim(seed: &mut u32) -> usize {
    let span = MAZE_DIM_MAX - MAZE_DIM_MIN + 1;
    MAZE_DIM_MIN + ((next_rand(seed) as usize) % span)
}

fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        WEST => EAST,
        UP => DOWN,
        DOWN => UP,
        _ => NORTH,
    }
}

fn neighbor(id: usize, d: usize, sx: usize, sy: usize, sz: usize) -> Option<usize> {
    let plane = sx * sy;
    let z = id / plane;
    let rem = id % plane;
    let y = rem / sx;
    let x = rem % sx;

    match d {
        NORTH if y > 0 => Some(id - sx),
        EAST if x + 1 < sx => Some(id + 1),
        SOUTH if y + 1 < sy => Some(id + sx),
        WEST if x > 0 => Some(id - 1),
        UP if z + 1 < sz => Some(id + plane),
        DOWN if z > 0 => Some(id - plane),
        _ => None,
    }
}

fn parse_dir(dir: u32) -> Option<usize> {
    match dir {
        0 => Some(NORTH),
        1 => Some(EAST),
        2 => Some(SOUTH),
        3 => Some(WEST),
        4 => Some(UP),
        5 => Some(DOWN),
        _ => None,
    }
}

fn node_types(seed: u32, exits: &[u8], on_path: &[u8], goal: usize) -> Result<KVVec<NodeType>> {
    let count = exits.len();
    let mut out = KVVec::with_capacity(count, GFP_KERNEL)?;

    for id in 0..count {
        let kind = if id == goal {
            NodeType::Goal
        } else if id == 0 || on_path[id] != 0 {
            NodeType::None
        } else {
            // Off-path branches remain navigable; only dead-end leaves may be spikes.
            let degree = exits[id].count_ones();
            if degree == 1 && dead_end_is_spike(seed, id) {
                NodeType::Spikes
            } else {
                NodeType::None
            }
        };

        out.push(kind, GFP_KERNEL)?;
    }

    Ok(out)
}

fn dead_end_is_spike(seed: u32, id: usize) -> bool {
    let mut x = seed ^ (id as u32).wrapping_mul(0x9E37_79B9);
    x ^= x >> 16;
    x = x.wrapping_mul(0x7feb_352d);
    x ^= x >> 15;
    x = x.wrapping_mul(0x846c_a68b);
    x ^= x >> 16;
    (x & 1) == 0
}

fn build_flag() -> [u8; CHAL_FLAG_LEN] {
    let mut out = [0u8; CHAL_FLAG_LEN];
    let len = core::cmp::min(FLAG_VALUE.len(), CHAL_FLAG_LEN);
    out[..len].copy_from_slice(&FLAG_VALUE[..len]);
    out
}
