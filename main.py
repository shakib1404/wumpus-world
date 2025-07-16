from game_interface import ModernWumpusWorldGUI

def parse_grid_from_file(file_path):
    with open(file_path, "r") as file:
        return [list(line.strip()) for line in file if line.strip()]

def main():    
    print("Starting Wumpus World - AI Agent Navigation")
    print("=" * 50)
    
    grid_file_path = "grid2.txt"
    
    grid = parse_grid_from_file(grid_file_path)
    print("Parsed Grid:")
    for row in grid:
        print(row)
    
    gui = ModernWumpusWorldGUI(grid)
    gui.run()

if __name__ == "__main__":
    main()