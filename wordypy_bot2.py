#!/usr/bin/env python3
"""
WordyPy Game: An AI bot that plays a Wordle-like game.

This script contains all the necessary classes to run a game of WordyPy,
where an AI `Bot` attempts to guess a secret five-letter word. The `GameEngine`
provides feedback for each guess as an image, which the `Bot` must process
to make smarter guesses in subsequent rounds.

Classes:
    Letter: Represents a single letter in a guess and its feedback.
    DisplaySpecification: Holds configuration for the visual feedback image.
    Bot: The AI agent that processes image feedback and makes guesses.
    GameEngine: Controls the game flow, generates the target word, and creates
                the feedback images.
"""

# 1. Standard library imports
import random

# 2. Related third-party imports
from PIL import Image, ImageDraw, ImageFont


class Letter:
    """A class representing a letter in a word game. [cite: 2]
    
    This class acts as a data structure to hold a single character from a guess
    and the results of that guess (e.g., if it's in the word, if it's in the
    correct position). [cite: 2]

    Attributes:
        letter (str): The character itself (e.g., 'A').
        in_word (bool): True if the letter is in the target word.
        in_correct_place (bool): True if the letter is in the correct position.
    """

    def __init__(self, letter: str) -> None:
        """
        Initializes the Letter object with a character.
        
        __init__(self, letter: str): This is the constructor. 
        When you create a Letter object, you give it a character (e.g., 'A'), 
        which it stores in self.letter. The feedback attributes in_word and 
        in_correct_place are initialized to False because their true status is not known yet. 
        """
        self.letter: str = letter
        
        # The status flags start as False because the feedback for this letter
        # is unknown until the GameEngine evaluates it.
        self.in_word: bool = False
        self.in_correct_place: bool = False

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation for debugging.
        
        __repr__(self): This is a special method that provides a "representation" 
        of the object. It's extremely useful for debugging, as it allows you to print() 
        a Letter object and get a clear, descriptive output.
        
        --- In a new Jupyter cell for testing ---
        1. Create an instance of your Letter class
        test_letter = Letter('A')

        2. Change its state for the test
        test_letter.in_word = True

        3. Just type the variable name on the last line
        test_letter
        
        --- In the code for debugging ---
        test_letter = Letter('B')
        test_letter.in_correct_place = True

        Option 1: Using the repr() function
        print(repr(test_letter))

        Option 2: Using an f-string with the !r flag
        print(f"Debugging letter object: {test_letter!r}")
        *** The !r in the f-string is a special command that tells Python to use the __repr__ output for that variable. ***
        """
        return f"Letter('{self.letter}', in_word={self.in_word}, in_correct_place={self.in_correct_place})"
    
    def is_in_word(self) -> bool:
        """
        Returns the status of the in_word flag.
        
        is_in_word(self) and is_in_correct_place(self): These are simple "getter" methods. 
        They don't change anything; they just return the current boolean value of their 
        corresponding attribute. The GameEngine uses these methods to check the feedback 
        for each letter when rendering the result image. 
        """
        return self.in_word

    def is_in_correct_place(self) -> bool:
        """Returns the status of the in_correct_place flag. """
        return self.in_correct_place


class DisplaySpecification:
    """
    A dataclass for holding display specifications for WordyPy.
    
    This class groups all the constants that control the visual appearance
    of the feedback images, such as block sizes and color codes.
    
    Attributes:
        - block_width: the width of each character in pixels
        - block_height: the height of each character in pixels
        - correct_location_color: the hex code to color the block when it is correct
        - incorrect_location_color: the hex code to color the block when it is in the wrong location but exists in the string
        - incorrect_color: the hex code to color the block when it is not in the string
        - space_between_letters: the amount of padding to put between characters, in pixels
        - word_color: the hex code of the background color of the string
    """
    # --- Sizing Attributes (in pixels) ---
    block_width: int = 80
    block_height: int = 80
    space_between_letters: int = 5

    # --- Color Attributes (as hex strings) ---
    correct_location_color: str = "#00274C"
    incorrect_location_color: str = "#FFCB05"
    incorrect_color: str = "#D3D3D3"
    word_color: str = "#FFFFFF"


class Bot:
    """The AI agent that processes image feedback and makes guesses."""

    def __init__(self, word_list_file: str, display_spec: DisplaySpecification) -> None:
        """
        Initializes the Bot with a list of possible words and display specs.

        The __init__ method is the setup phase for your bot. When a Bot object is created, this code runs once:
            1) It receives the path to the word file (word_list_file) and the visual settings (display_spec).
            2) It creates an empty list called self.word_list that will hold all valid guesses.
            3) It opens the word file, reads it line by line, and adds each cleaned-up (.strip().upper()) word to self.word_list.
            4) Finally, it stores the display_spec object in self.display_spec so other methods 
               in the bot can access the color and size information when processing the feedback images.

        Args:
            word_list_file [str]: The path to the text file containing valid words.
            display_spec (DisplaySpecification): An object containing visual settings.
        """
        # This list will hold all words the bot considers possible answers.
        # It is filtered down after each guess.
        self.word_list: list[str] = []
        
        # with open(...) ensures the file is closed automatically after reading.
        with open(word_list_file, 'r') as file:
            for word in file:
                # .strip() removes whitespace/newlines and .upper() ensures
                # all words are uppercase to match the GameEngine's format.
                self.word_list.append(word.strip().upper())
        
        # Store the display specification object for use in image processing.
        self.display_spec: DisplaySpecification = display_spec

    @staticmethod
    def _tuple_to_str(pixels: tuple) -> str:
        """
        Converts an RGB tuple to an uppercase hex color string.
        
        @staticmethod: This decorator declares _tuple_to_str as a static method. 
        This is appropriate because the conversion logic doesn't need any information 
        from a Bot instance (it doesn't need self).

        In Python, a single leading underscore in a method or attribute name (like _tuple_to_str) 
        is a convention. It signals to other programmers that this method is intended for internal 
        use only within the class and should not be called directly from outside the class.

        This is a static helper method as it does not depend on any
        specific Bot instance's state. It only considers the first three
        values of the tuple (R, G, B) and ignores any fourth (alpha) value.

        Args:
            pixels (tuple): An RGB or RGBA tuple (e.g., (0, 39, 76)).

        Returns:
            str: The uppercase hex string representation (e.g., "#00274C").        
        """
        # Unpack the first three values from the tuple into r, g, and b variables.
        # pixels[:3] ensures we ignore the alpha channel if it exists.
        r, g, b = pixels[:3]

        # Use an f-string to format each value as a two-digit hexadecimal number
        # and join them together with a leading '#'.
        # :02x formats a number as a 2-digit, zero-padded, lowercase hex.
        # .upper() converts the final string to uppercase as required.
        return f"#{r:02x}{g:02x}{b:02x}".upper()
    
    def _process_image(self, guess: str, guess_image: Image) -> list[Letter]:
        """
        Processes the feedback image to determine the status of each letter.

        This method iterates through the five letter positions of the guess,
        samples a pixel from the corresponding colored block in the feedback
        image, and translates that color into the correct feedback flags
        (in_word, in_correct_place) for a Letter object.

        Args:
            guess (str): The word that was guessed (e.g., "PYTHON").
            guess_image (Image): The PIL Image object returned by the GameEngine.

        Returns:
            list[Letter]: A list of five Letter objects with their feedback
                          flags correctly set.
        """
        feedback_list = []

        # Get dimensions and colors from the display spec for easier access.
        block_w = self.display_spec.block_width
        spacing = self.display_spec.space_between_letters
        correct_color_hex = self.display_spec.correct_location_color.upper()
        wrong_loc_color_hex = self.display_spec.incorrect_location_color.upper()
        
        # Loop five times, once for each character in the guess.
        for i, char in enumerate(guess):
            x = 5 + i * (block_w + spacing)
            y = 5

            # Get the color of the pixel at that coordinate.
            pixel_color_tuple = guess_image.getpixel((x, y))
            # Convert the color from an (R,G,B) tuple to a hex string.
            pixel_color_hex = Bot._tuple_to_str(pixel_color_tuple)
            
            # Create a new Letter object for the character of the current guess.
            letter_obj = Letter(char)

            # Compare the sampled color to the known feedback colors.
            if pixel_color_hex == correct_color_hex:
                letter_obj.in_correct_place = True
                letter_obj.in_word = True
            elif pixel_color_hex == wrong_loc_color_hex:
                letter_obj.in_word = True
            
            # Add the configured Letter object to our results list.
            feedback_list.append(letter_obj)
        
        return feedback_list
    
    def make_guess(self) -> str:
        """
        Selects and returns a single word from the current list of possibilities.

        This method is called by the GameEngine at the start of each turn.

        This method is called once per turn by the GameEngine. It simply 
        reaches into its self.word_list attribute, randomly selects one word, 
        and returns it. Early in the game, this guess is very random. 
        Later in the game, after record_guess_results has filtered the list down 
        to just a few possibilities, this "random" choice is actually a highly educated guess.
        
        Returns:
            str: The bot's next guess.
        """
        # Use the random.choice() function to pick one word from the list
        # of words the bot currently thinks are possible.
        return random.choice(self.word_list)

    def record_guess_results(self, guess: str, guess_image: Image) -> None:
        """Filters the bot's word list based on guess feedback.

        This method is the core logic of the bot. It processes the feedback
        image, then iterates through its list of possible words, eliminating
        any word that violates the rules learned from the feedback.

        Args:
            guess (str): The word that was just guessed.
            guess_image (Image): The feedback image from the GameEngine.
        """
        # First, convert the feedback image into a structured list of Letter objects.
        guess_results = self._process_image(guess, guess_image)

        # Remove the guessed word from the list to prevent repeats.
        if guess in self.word_list:
            self.word_list.remove(guess)
        
        # Create a new, empty list to hold only the words that pass all the rules.
        new_possible_words = []

        # Check every remaining word against the feedback from the last guess.        
        for word in self.word_list:
            is_still_possible = True

            # This inner loop checks the current 'word' against each letter's feedback.            
            for i, feedback in enumerate(guess_results):
                char_in_guess = feedback.letter

                # Rule 1: Green letters (correct letter, correct place)
                if feedback.is_in_correct_place():
                    if word[i] != char_in_guess:
                        is_still_possible = False
                        break # This word is invalid.
                
                # Rule 2: Yellow letters (correct letter, wrong place)
                elif feedback.is_in_word():
                    if char_in_guess not in word or word[i] == char_in_guess:
                        is_still_possible = False
                        break  # This word is invalid.
                
                # Rule 3: Grey letters (incorrect letter)
                else:
                    # A grey letter can be eliminated ONLY if it doesn't also appear
                    # as a green or yellow in the SAME guess (e.g., guess "ARRAY" for target "ALARM").
                    is_positive_somewhere = any(
                        char_in_guess == f.letter and f.is_in_word() for f in guess_results
                    )
                    if not is_positive_somewhere and char_in_guess in word:
                        is_still_possible = False
                        break  # This word is invalid.
            
            # If the word survived all the checks, add it to our new list.
            if is_still_possible:
                new_possible_words.append(word)
        
        # Finally, replace the old word list with the newly filtered, smaller list.
        self.word_list = new_possible_words

class GameEngine:
    """The GameEngine represents a new WordPy game to play."""

    def __init__(self, display_spec: DisplaySpecification = None) -> None:
        """Creates a new WordyPy game engine. If the game_spec is None then
        the engine will use the default color and drawing values, otherwise
        it will override the defaults using the provided specification
        """
        # det the display specification to defaults or user provided values
        if display_spec == None:
            display_spec = DisplaySpecification()
        self.display_spec = display_spec

        self.err_input = False
        self.err_guess = False
        self.prev_guesses = []  # record the previous guesses

    def play(
        self, bot: Bot, word_list_file: str = "words.txt", target_word: str = None
    ) -> Image:
        """Plays a new game, using the supplied bot. By default the GameEngine
        will look in words.txt for the list of allowable words and choose one
        at random. Set the value of target_word to override this behavior and
        choose the word that must be guessed by the bot.
        """

        def format_results(results) -> str:
            """Small function to format the results into a string for quick
            review by caller.
            """
            response = ""
            for letter in results:
                if letter.is_in_correct_place():
                    response = response + letter.letter
                elif letter.is_in_word():
                    response = response + "*"
                else:
                    response = response + "?"
            return response

        # read in the dictionary of allowable words
        # FIX: Use list[str] instead of list(str)
        word_list: list[str] = list(
            map(lambda x: x.strip().upper(), open(word_list_file, "r").readlines())
        )
        
        # record the known correct positions
        # FIX: Use list[str | None] for a list that can hold both strings and None
        known_letters: list[str | None] = [None, None, None, None, None]
        # set of unused letters
        unused_letters = set()

        # assign the target word to a member variable for use later
        if target_word is None:
            target_word = random.choice(word_list).upper()
        else:
            target_word = target_word.upper()
            if target_word not in word_list:
                print(f"Target word {target_word} must be from the word list")
                self.err_input = True
                return

        print(
            f"Playing a game of WordyPy using the word list file of {word_list_file}.\nThe target word for this round is {target_word}\n"
        )

        MAX_GUESSES = 6
        for i in range(1, MAX_GUESSES):
            # ask the bot for it's guess and evaluate
            guess: str = bot.make_guess()

            # print out a line indicating what the guess was
            print(f"Evaluating bot guess of {guess}")

            if guess not in word_list:
                print(f"Guessed word {guess} must be from the word list")
                self.err_guess = True
            elif guess in self.prev_guesses:
                print(f"Guess word cannot be the same one as previously used!")
                self.err_guess = True

            if self.err_guess:
                return

            self.prev_guesses.append(guess)  # record the previous guess
            for j, letter in enumerate(guess):
                if letter in unused_letters:
                    print(
                        f"The bot's guess used {letter} which was previously identified as not used!"
                    )
                    self.err_guess = True
                if known_letters[j] is not None:
                    if letter != known_letters[j]:
                        print(
                            f"Previously identified {known_letters[j]} in the correct position is not used at position {j}!"
                        )
                        self.err_guess = True

                if self.err_guess:
                    return

            # get the results of the guess
            correct, results = self._set_feedback(guess, target_word)

            # print out a line indicating whether the guess was correct or not
            print(f"Was this guess correct? {correct}")

            # get the image to be returned to the caller
            img = self._format_results(results)

            print(f"Sending guess results to bot:\n")
            # display(img) -- commented out to avoid issues in non-notebook environments
            img.show() # This will open the image in the default image viewer

            bot.record_guess_results(guess, img)

            # if they got it correct we can just end
            if correct:
                print(f"Great job, you found the target word in {i} guesses!")
                return

        # if we get here, the bot didn't guess the word
        print(
            f"Thanks for playing! You didn't find the target word in the number of guesses allowed."
        )
        return

    def _set_feedback(self, guess: str, target_word: str) -> tuple[bool, list[Letter]]:
        # whether the complete guess is correct
        # set it to True initially and then switch it to False if any letter doesn't match
        correct: bool = True

        letters = []
        for j in range(len(guess)):
            # create a new Letter object
            letter = Letter(guess[j])

            # check to see if this character is in the same position in the
            # guess and if so set the in_correct_place attribute
            if guess[j] == target_word[j]:
                letter.in_correct_place = True
            else:
                # we know they don't have a perfect answer, so let's update
                # our correct variable for feedback
                correct = False

            # check to see if this character is anywhere in the word
            if guess[j] in target_word:
                letter.in_word = True

            # add this letter to our list of letters
            letters.append(letter)

        return correct, letters

    def _render_letter(self, letter: Letter) -> Image:
        """This function renders a single Letter object as an image."""
        # set color string as appropriate
        color: str = self.display_spec.incorrect_color
        if letter.is_in_correct_place():
            color = self.display_spec.correct_location_color
        elif letter.is_in_word():
            color = self.display_spec.incorrect_location_color

        # now we create a new image of width x height with the given color
        block = Image.new(
            "RGB",
            (self.display_spec.block_width, self.display_spec.block_height),
            color=color,
        )
        # and we actually render that image and get a handle back
        draw = ImageDraw.Draw(block)

        # for the lettering we need to identify the center of the block,
        # so we calculate that as the (X,Y) position to render text
        X: int = self.display_spec.block_width // 2
        Y: int = self.display_spec.block_height // 2

        # we will create a font object for drawing lettering
        FONT_SIZE: int = 50
        font = ImageFont.truetype(r"C:\Users\ntune\AppData\Local\Microsoft\Windows\Fonts\Roboto-Bold.ttf", FONT_SIZE)

        # now we can draw the letter and tell PIL we want to have the
        # character centered in the box using the anchor attribute
        draw.text((X, Y), letter.letter, size=FONT_SIZE, anchor="mm", font=font)

        return block

    def _format_results(self, letters: list[Letter]) -> Image:
        """This function does the hard work of converting the list[Letter]
        for a guess into an image.
        """
        # some constants that determine what a word of these letters
        # will look like. The algorithm for rendering a word is that
        # we will render each letter independently and put some spacing between
        # them. This means the total word width is equal to the size of
        # all of the letters and the spacing, and the word height is equal
        # to the size of just a single letter
        WORD_WIDTH: int = (len(letters) * self.display_spec.block_width) + (
            len(letters) - 1
        ) * self.display_spec.space_between_letters
        WORD_HEIGHT: int = self.display_spec.block_height

        # we can use the paste() function to place one PIL.Image on top
        # of another PIL.Image
        word = Image.new(
            "RGB", (WORD_WIDTH, WORD_HEIGHT), color=self.display_spec.word_color
        )
        curr_loc = 0
        for letter in letters:
            # we can render the letter and then paste, setting the location
            # as X,Y position we want to paste it in
            rendered_letter: Image = self._render_letter(letter)
            word.paste(rendered_letter, (curr_loc, 0))
            curr_loc += (
                self.display_spec.block_width + self.display_spec.space_between_letters
            )

        return word

if __name__ == "__main__":
    # Chris's favorite words
    favorite_words = ["doggy", "drive", "daddy", "field", "state"]

    # Write this to a temporary file
    words_file = "temp_file.txt"
    with open(words_file, "w") as file:
        file.writelines("\n".join(favorite_words))

    # Create a new GameEngine with the default DisplaySpecification
    ge = GameEngine()

    # Initialize the student Bot using the display specification from the game engine object
    bot = Bot(words_file, ge.display_spec)

    # Play a game with the Bot
    ge.play(bot, word_list_file=words_file)


