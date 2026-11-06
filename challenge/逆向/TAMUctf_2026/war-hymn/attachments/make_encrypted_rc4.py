




def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0

    # KSA
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xff
        S[i], S[j] = S[j], S[i]

    # PRGA
    i = j = 0
    out = bytearray()
    for byte in data:
        i = (i + 1) & 0xff
        j = (j + S[i]) & 0xff
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) & 0xff]
        out.append(byte ^ K)

    return bytes(out)


def dump_c_array(name, data):
    print(f"unsigned char {name}[] = {{")
    print(", ".join(f"0x{b:02x}" for b in data))
    print("};\n")


if __name__ == "__main__":
    key = b"AggiesAggiesAggies"

    decoy1 = b"Yeah, this aint it"
    decoy2 = b"Keep going bruh"
    decoy3 = b"Are we there yet?"
    flag   = b"gigem{sh0uld_h4v3_r4n_th3_b411_0n_f1r$t_4nd_g04l!!!}"

    dump_c_array("enc_decoy1", rc4(key, decoy1))
    dump_c_array("enc_decoy2", rc4(key, decoy2))
    dump_c_array("enc_decoy3", rc4(key, decoy3))
    dump_c_array("enc_flag",   rc4(key, flag))
