import sys
from topsis_rhythm_102303707.engine import run_topsis

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")
        return

    try:
        run_topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        print("TOPSIS completed successfully 🎉")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
