"""
DerivaDEX signature utils
"""
from coincurve import PublicKey, PrivateKey
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import keccak


def encrypt_with_nonce(encryption_key: str, msg: str) -> bytes:
    network_public_key = PublicKey(bytes.fromhex(encryption_key[2:]))
    my_secret_key = PrivateKey(get_random_bytes(32))
    my_public_key = my_secret_key.public_key
    shared_pub = network_public_key.multiply(my_secret_key.secret)
    keccak_256 = keccak.new(digest_bits=256)
    keccak_256.update(shared_pub.format())
    derived_key = keccak_256.digest()[:16]
    nonce = get_random_bytes(12)

    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=nonce)
    encoded_message = msg.encode("utf8")
    ciphertext, tag = cipher.encrypt_and_digest(
        len(encoded_message).to_bytes(4, byteorder="big") + encoded_message
    )

    return ciphertext + tag + nonce + my_public_key.format()
