import cryptography.exceptions
import os
import ellipticcurve
import numbertheory
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric import ed25519


# Key exchange of this work is computed on secp256k1

# secp256k1 elliptic curve equation: y² = x³ + 7
# Prime of the finite field
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
# Define curve secp256k1
secp256k1 = ellipticcurve.CurveFp(P, 0, 7)
# Generator point of secp256k1
G = ellipticcurve.Point(
    x=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    y=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    curve=secp256k1
)
# Order of the group generated by G, such that nG = Infinity
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Name the user and generate user signing and verification key
class User:
    def __init__(self, name):
        self.name = name
        self.signing_key = bytes
        self.verification_key = bytes


    # User generate signing and verification keys
    def generate_Ed25519_key(self):
        self.signing_key = ed25519.Ed25519PrivateKey.generate()
        self.verification_key = self.signing_key.public_key()

    # User generates a random private number r and a public point value r * G, they will be used for key exchange
    def ephemeral_value(self):
        self.ephemeral_private_value = int.from_bytes(os.urandom(32), 'big')
        self.ephemeral_public_value = self.ephemeral_private_value * G
        self.inverse_ephemeral_private_value = numbertheory.inverse_mod(self.ephemeral_private_value, N)

    # User generates shared key
    def exchange(self, private_value, public_value, sid):
        self.shared_key = private_value * public_value
        self.derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data'
        ).derive(
            bytes('1' + str(self.shared_key._Point__x) + str(self.shared_key._Point__y) + str(sid), 'utf-8'))
        self.key_confirmation = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data'
        ).derive(
            bytes('2' + str(self.shared_key._Point__x) + str(self.shared_key._Point__y) + str(sid), 'utf-8'))

    # User signs data
    def sign(self, data):
        signature = self.signing_key.sign(
            transfer_to_bytes(data)
        )
        return signature

# Transfer data to bytes
def transfer_to_bytes(data):
    temp_data = ''
    for info in data:
        if type(info) == ellipticcurve.Point:
            temp_data = temp_data + str(info._Point__x) + str(info._Point__y)
        if type(info) == int:
            temp_data = temp_data + str(info)
        if type(info) == str:
            temp_data = temp_data + info
    return bytes(temp_data, 'utf-8')

# Verify if data and signature are signed by User
def verify(verification_key, data, signature):
    verify = True
    try:
        verification_key.verify(
            signature,
            transfer_to_bytes(data)
        )
    except cryptography.exceptions.InvalidSignature:
        verify = False
    return verify
