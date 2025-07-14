# main.py
"""
Wumpus World - AI Agent Navigation
Main entry point for the application
"""

from game_interface import ModernWumpusWorldGUI

def parse_grid_from_file(file_path):
    """Read and parse the grid input from a file"""
    with open(file_path, "r") as file:
        return [list(line.strip()) for line in file if line.strip()]

def main(): 
    """Main function to run the Wumpus World game"""
    print("Starting Wumpus World - AI Agent Navigation")
    print("=" * 50)
    
    # File path for the grid input
    grid_file_path = "grid3.txt"  # Ensure this file exists in the same directory
    
    # Parse the grid from the file
    grid = parse_grid_from_file(grid_file_path)
    print("Parsed Grid:")
    for row in grid:
        print(row)
    
    # Create and run the GUI
    gui = ModernWumpusWorldGUI(grid)
    gui.run()

if __name__ == "__main__":
    main()