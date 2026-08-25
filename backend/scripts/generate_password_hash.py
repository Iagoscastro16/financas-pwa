"""Gera o hash bcrypt de uma senha para colocar em AUTH_PASSWORD_HASH no .env.

Uso:
    python scripts/generate_password_hash.py
"""

from getpass import getpass

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main() -> None:
    senha = getpass("Digite a senha desejada: ")
    confirmacao = getpass("Confirme a senha: ")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")
    print("\nAUTH_PASSWORD_HASH=" + pwd_context.hash(senha))


if __name__ == "__main__":
    main()
