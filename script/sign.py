#!/usr/bin/env python3

from argparse import ArgumentParser
from git import Repo
from stellar_sdk import Server, TransactionBuilder, Network, TransactionEnvelope
from subprocess import check_call


SERVER = Server('https://horizon.stellar.org')
NETWORK_PASSPHRASE = Network.PUBLIC_NETWORK_PASSPHRASE
BASE_FEE = 100


MTL_ADDRESS = 'GDX23CPGMQ4LN55VGEDVFZPAJMAUEHSHAMJ2GMCU2ZSHN5QF4TMZYPIS'


def parse_args():
    parser = ArgumentParser(description='MTL document signing tool')
    subparsers = parser.add_subparsers(help='subcommand', dest='subcommand')

    sign = subparsers.add_parser('sign')
    sign.add_argument('commit')

    check = subparsers.add_parser('check')
    check.add_argument('tx')

    return parser.parse_args()


def make_sign_tx(commit_ref: str):
    repo = Repo('.')
    commit_hash = bytes.fromhex(repo.git.rev_parse(commit_ref))
    commit_hash_len = len(commit_hash)
    assert commit_hash_len == 32, commit_hash_len
    payload = bytes([1]) + commit_hash[:31]
    mtl_account = SERVER.load_account(MTL_ADDRESS)
    return (
        TransactionBuilder(
            source_account=mtl_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=BASE_FEE,
        )
        .set_timeout(60 * 60 * 24)
        .add_hash_memo(payload)
        .build()
    )


def check_tx(tx: str):
    memo: bytes = (
        TransactionEnvelope
        .from_xdr(tx, NETWORK_PASSPHRASE)
        .transaction
        .memo
        .memo_hash
    )
    version = memo[0]
    if version == 1:
        commit_hex = memo[1:].hex()
        check_call(['git', 'show', '--stat', commit_hex])
    else:
        raise ValueError('Bad version', version)


def main():
    args = parse_args()
    if args.subcommand == 'sign':
        print(make_sign_tx(args.commit).to_xdr())
    elif args.subcommand == 'check':
        check_tx(args.tx)


if __name__ == '__main__':
    main()
