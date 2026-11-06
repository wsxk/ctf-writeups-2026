#include <windows.h>
#include <stdio.h>

// xor buffer with user-provided 1 byte key.
void singleXorBuf(BYTE* pBuf, DWORD dwLen) {
    if (pBuf == NULL || dwLen == 0) return;

    int inputKey = 0;

    // Prompting for the 1-byte XOR key

    // Capture the first byte of input
    inputKey = getchar();

    // Clear the rest of the stdin buffer to avoid leftover characters
    if (inputKey != '\n' && inputKey != EOF) {
        int c;
        while ((c = getchar()) != '\n' && c != EOF);
    }

    unsigned char key = (unsigned char)inputKey;

    // Perform the XOR operation
    for (DWORD i = 0; i < dwLen; i++) {
        pBuf[i] ^= key;
    }
}

// Copies filename0.exe to filename1.exe, where the number is incremented by 1. If filename9.exe is detected, it will be renamed to filename10.exe.
// writes the destination path to the provided buffer (szDestPath)
void cloneToDisk(char szDestPath[MAX_PATH]) {
    char szSourcePath[MAX_PATH];

    // 1. Get current running path
    DWORD pathLen = GetModuleFileNameA(NULL, szSourcePath, MAX_PATH);
    if (pathLen == 0) return;

    // Copy source to destination so we can modify the destination only
    strcpy_s(szDestPath, MAX_PATH, szSourcePath);

    // 2. Find the digit (assuming format: nameN.exe)
    // Index: [pathLen - 5] is the character before ".exe"
    int digitIdx = pathLen - 5;
    char digit = szDestPath[digitIdx];

    if (digit < '0' || digit > '9') {
        return;
    }

    if (digit == '9') {
        // Handle 9 -> 10 transition
        // We replace the '.exe' part with '10.exe'
        snprintf(&szDestPath[digitIdx], MAX_PATH - digitIdx, "10.exe");
    }
    else {
        // Simple increment
        szDestPath[digitIdx] = digit + 1;
    }


    if (CopyFileA(szSourcePath, szDestPath, FALSE)) {
    }
    else {
    }
}

void packToResource(char szDestPath[MAX_PATH]) {
    char szSourcePath[MAX_PATH];
    HANDLE hFile = INVALID_HANDLE_VALUE;
    DWORD dwFileSize = 0;
    BYTE* lpBuffer = NULL;
    DWORD dwBytesRead = 0;

    // 1. Get the path of the currently running EXE
    if (GetModuleFileNameA(NULL, szSourcePath, MAX_PATH) == 0) {
        printf("Failed to get source path. Error: %lu\n", GetLastError());
        return;
    }

    // 2. Open the current EXE for reading
    hFile = CreateFileA(szSourcePath, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        printf("Failed to open source for reading. Error: %lu\n", GetLastError());
        return;
    }

    // 3. Allocate memory and read the file content
    dwFileSize = GetFileSize(hFile, NULL);
    lpBuffer = (BYTE*)malloc(dwFileSize);
    if (lpBuffer == NULL) {
        CloseHandle(hFile);
        return;
    }

    if (!ReadFile(hFile, lpBuffer, dwFileSize, &dwBytesRead, NULL)) {
        printf("Failed to read file. Error: %lu\n", GetLastError());
        free(lpBuffer);
        CloseHandle(hFile);
        return;
    }
    CloseHandle(hFile);

	// xor encode the buffer with user-provided key
	singleXorBuf(lpBuffer, dwBytesRead);

    // 4. Start the Resource Update process on the destination EXE
    // FALSE here means we do NOT discard existing resources
    HANDLE hUpdate = BeginUpdateResourceA(szDestPath, FALSE);
    if (hUpdate == NULL) {
        free(lpBuffer);
        return;
    }

    // 5. Add the binary data as a resource
    // RT_RCDATA is a standard type for raw binary data
    // Name it "PAYLOAD" (ID: 101)
    if (UpdateResourceA(hUpdate,
        RT_RCDATA,
        MAKEINTRESOURCEA(101),
        MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
        lpBuffer,
        dwFileSize))
    {
        // 6. Commit the changes
        if (EndUpdateResource(hUpdate, FALSE)) {
        }
        else {
        }
    }
    else {
        EndUpdateResource(hUpdate, TRUE); // Discard changes on failure
    }

    free(lpBuffer);
}

int main() {
    char szDestPath[MAX_PATH];
	cloneToDisk(szDestPath);
	packToResource(szDestPath);
    return 0;
}