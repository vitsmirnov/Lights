"""
(c) Vitaly Smirnov [VSdev]
mrmaybelately@gmail.com
https://github.com/vitsmirnov
2024
"""

from lights_game import LightsGame


def main() -> None:
    try:
        game = LightsGame()
        game.run()
    except:  # Is it useless?
        print("An unexpected error has occured.")

    print("\n--- Done, bye! ---\n")


if __name__ == '__main__':
    main()
