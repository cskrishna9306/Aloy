# Import custom modules
from src.aloy.agent import Aloy
from src.aloy.config import config

def main():
    """
    The main entry point for Aloy.
    """
    
    # Define the Aloy instance, but this could potentially be inefficient
    # if we are creating this everytime the main() function is called
    aloy = Aloy()

    # No parameters need to be passed since all the workflow is pretty systematic
    aloy.run()

    return

if __name__ == "__main__":
    # My assumption is none of this can be async b/c we want Alexa to get
    # synchronous results
    main()

