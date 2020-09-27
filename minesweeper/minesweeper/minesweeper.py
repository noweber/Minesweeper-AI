import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        # Note there is no need to assert len(self.cells) > 0 in many methods
        # since self.cells is initialized as an empty set as part of the class invariant.
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        # Any time the number of cells is equal to the count,
        # we know that all of that sentence’s cells must be mines.
        if len(self.cells) == self.count:
            return self.cells
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        # Any time we have a sentence whose count is 0,
        # we know that all of that sentence’s cells must be safe.
        if self.count is 0:
            return self.cells
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        # If our AI knew the sentence {A, B, C} = 2, and we were told that C is a mine,
        # we could remove C from the sentence and decrease the value of count (since C was a mine that contributed to that count),
        # giving us the sentence {A, B} = 1. This is logical: 
        # if two out of A, B, and C are mines, and we know that C is a mine, 
        # then it must be the case that out of A and B, exactly one of them is a mine.
        if cell in self.cells:
            # If the mine is in the Sentence, remove it and decrement the count.
            self.cells.remove(cell)
            self.count = self.count - 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        # For example, if our AI knew the sentence {A, B, C} = 2, we don’t yet have enough information to conclude anything.
        # But if we were told that C were safe, we could remove C from the sentence altogether,
        # leaving us with the sentence {A, B} = 2 (which, incidentally, does let us draw some new conclusions.)
        if cell in self.cells:

            # If the cell is safe, we can simply remove it from the sentence per the above example.
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        # 1) Mark the cell as a move that has been made:
        self.moves_made.add(cell)

        # 2) Mark the cell as safe:
        self.mark_safe(cell)

        # 3) Add a new sentence to the AI's knowledge base based on the value of `cell` and `count`
        self.knowledge.append(Sentence(self.__get_neighbors(cell), count))
        
        # 4 & 5: within do-while loop (will always execute at least once)
        while True: 
            original_knowledge = self.knowledge.copy()
            self.__infer_new_knowledge()
            if len(original_knowledge) is len(self.knowledge):
                # Then no new knowledge has been inferred
                break

    def __infer_new_knowledge(self):
        """
        Private method to infer new knowledge using the existing knowledge set.
        Return value is void, but this method will update sentences within self.knowledge or add any inferred sentences.
        """
        # 4) Mark any additional cells as safe or as mines if it can be concluded based on the AI's knowledge base
        for safe in self.safes:
            self.mark_safe(safe)    # This will update all sentences for any known safes.
        for mine in self.mines:
            self.mark_mine(mine)    # This will update all sentences for any known mines.
        for sentence in self.knowledge:
            self.safes = self.safes.union(sentence.known_safes())   # This will add any newly discovered safes.
            self.mines = self.mines.union(sentence.known_mines())   # This will add any newly discovered mines.

        # 5: Any time we have two sentences set1 = count1 and set2 = count2 where set1 is a subset of set2, then we can construct the new sentence set2 - set1 = count2 - count1.
        # Note: need to use a new list here else the current list of sentences could grow while iterating through it (it happened :))
        inferred_knowledge = []
        for sentence1 in self.knowledge:
            set1 = sentence1.cells
            for sentence2 in self.knowledge:
                set2 = sentence2.cells
                if set1 is not set2 and set1.issubset(set2): 
                    inferred_sentence = Sentence(set2 - set1, sentence2.count - sentence1.count)
                    if inferred_sentence not in inferred_knowledge:
                        # Avoid adding duplicate sentences as this will just slow things down.
                        inferred_knowledge.append(inferred_sentence)
        for sentence in inferred_knowledge:
            # Only add an inferred sentence if it is new knowledge.
            if sentence not in self.knowledge:
                self.knowledge.append(sentence)
        
    def __get_neighbors(self, cell):
        """
        Private method to retrieve all neighboring cells of a given cell.
        Returns a set of (i, j) 2-tuples representing the neighboring cells.
        """
        neighbors = set()
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    neighbors.add((i, j))
        return neighbors

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        # If there are no moves remaining, return None.
        if(self.__has_no_moves_remaining()):
            return None

        # Get the set of known safe moves
        safe_moves = self.safes - self.moves_made

        # Return None if there are no safe moves:
        if len(safe_moves) is 0:
            return None

        # Else return a random safe move:
        return random.sample(safe_moves, 1)[0]

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        if(self.__has_no_moves_remaining()):
            return None

        # Determine the remaining non-mine cell moves remaining:
        moves_remaining = set()
        for i in range(self.height):
            for j in range(self.width):
                if (i, j) in self.mines:
                    continue
                # No need to include moves which have already been made
                elif (i, j) in self.moves_made:
                    continue
                else:
                    moves_remaining.add((i, j))

        # Return a random element from the remaining moves:
        return random.sample(moves_remaining, 1)[0]
        
    def __has_no_moves_remaining(self):
        """
        Private (the Python version of private) method to determine whether or not any new moves can be made (without knowingly clicking a mine)
        Return true if there are no moves remaining (when every non-mine cell move has been made)
        Returns false if there are moves remaining.
        """
        return len(self.moves_made) + len(self.mines) is self.height * self.width
