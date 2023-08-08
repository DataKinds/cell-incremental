import signal

from game.world import World


def handle_pdb(sig, frame):
    import pdb

    dbg = pdb.Pdb()
    dbg.run('import os; os.system("reset")')
    dbg.set_trace(frame)


def entrypoint():
    print("I love you.")
    signal.signal(signal.SIGUSR1, handle_pdb)
    World().run()


if __name__ == "__main__":
    entrypoint()
