import random
from PIL import Image, ImageFont, ImageDraw

class Letter:
    '''A class representing a letter in a word game.'''

    def __init__(self, letter: str) -> None:
        """Initializes the Letter object."""
        self.letter: str = letter
        # These attribute names must match the tests EXACTLY
        self.in_word: bool = False
        self.in_correct_place: bool = False

    def __repr__(self) -> str:
        """Developer-friendly representation for debugging."""
        # This should also use the correct attribute names
        return f"Letter('{self.letter}', in_word={self.in_word}, in_correct_place={self.in_correct_place})"
    
    def is_in_word(self) -> bool:
        """Returns True if the letter is in the word (for the GameEngine)."""
        return self.in_word

    def is_in_correct_place(self) -> bool:
        """Returns True if the letter is in the correct place (for the GameEngine)."""
        return self.in_correct_place
    
# CELL

# This cell has the tests your Letter class

# Check if the Letter class exists
assert "Letter" in dir(), "The Letter class does not exist, did you define it?"

# Check to see if the Letter class can be created
l: Letter
try:
    l = Letter("s")
except:
    assert (
        False
    ), "Unable to create a Letter object with Letter('s'), did you correctly define the Letter class?"

# Check to see if the Letter class has the in_correct_place attribute
assert hasattr(
    l, "in_correct_place"
), "The letter object created has no in_correct_place attribute, but this should be False by default. Did you create this attribute?"

# CELL

class DisplaySpecification:
    """A dataclass for holding display specifications for WordyPy. The following
    values are defined:
        - block_width: the width of each character in pixels
        - block_height: the height of each character in pixels
        - correct_location_color: the hex code to color the block when it is correct
        - incorrect_location_color: the hex code to color the block when it is in the wrong location but exists in the string
        - incorrect_color: the hex code to color the block when it is not in the string
        - space_between_letters: the amount of padding to put between characters, in pixels
        - word_color: the hex code of the background color of the string
    """

    block_width: int = 80
    block_height: int = 80
    correct_location_color: str = "#00274C"
    incorrect_location_color: str = "#FFCB05"
    incorrect_color: str = "#D3D3D3"
    space_between_letters: int = 5
    word_color: str = "#FFFFFF"

# CELL

# Create the implementation of the Bot class here

# YOUR CODE HERE
class Bot:
    """The Bot class represents a bot that can play WordyPy."""
    
    def __init__(self, word_list_file: str, display_spec: DisplaySpecification) -> None:
        """Initializes the Bot with a list of possible words and a display specification."""
        # Load the word list from the provided file
        with open(word_list_file, 'r') as file:
            self.word_list = [line.strip().upper() for line in file.readlines()]
    
        self.display_spec = display_spec
        self.possible_words = self.word_list.copy()
        self.last_guess = None

    def _tuple_to_str(self, pixels: tuple) -> str:
        """Converts an RGB tuple to a hex color string."""
        # Example: (0, 39, 76) -> "#00274C"
        r, g, b = pixels
        return f"#{r:02x}{g:02x}{b:02x}".upper() # Format as hex and uppercase

    def _process_image(self, guess: str, guess_image: 'Image') -> list['Letter']:
        """Processes the guess image to extract letter feedback."""
        
        feedback = []
        
        # Get dimensions and colors from the display specification for easier access
        block_w = self.display_spec.block_width
        block_h = self.display_spec.block_height
        spacing = self.display_spec.space_between_letters
        
        correct_color = self.display_spec.correct_location_color
        wrong_loc_color = self.display_spec.incorrect_location_color
        
        # Loop through each of the 5 letters in the guess
        for i, char in enumerate(guess):
            # 1. Calculate the coordinates of the center of the current letter's block
            x = (block_w // 2) + i * (block_w + spacing)
            y = block_h // 2
            
            # 2. Get the color of the pixel at that coordinate
            pixel_color_tuple = guess_image.getpixel((x, y))
            pixel_color_hex = self._tuple_to_str(pixel_color_tuple)
            
            # 3. Create a Letter object and set its flags based on the color
            letter_obj = Letter(char)
            
            if pixel_color_hex == correct_color:
                letter_obj.is_in_correct_place = True
                letter_obj.is_in_word = True
            elif pixel_color_hex == wrong_loc_color:
                letter_obj.is_in_word = True
            
            # 4. Add the configured letter to our feedback list
            feedback.append(letter_obj)
            
        return feedback
    
    def make_guess(self) -> str:
        """Makes a random guess from the list of possible words."""
        guess = random.choice(self.word_list)
        return guess

    def record_guess_results(self, guess: str, guess_results: Image) -> None:
        """Records the results of a guess to refine future guesses."""
        # TODO: Wire up image processing to extract letter feedback
        guess_results = self._process_image(guess, guess_results)
        self.word_list.remove(guess)
        
        new_possible_words = []

        for word in self.word_list:
            is_still_possible = True

            for i, letter_feedback in enumerate(guess_results):
                letter_char = letter_feedback.letter
                
                if letter_feedback.is_in_correct_place():
                    if word[i] != letter_char:
                        is_still_possible = False
                        break
                elif letter_feedback.is_in_word():
                    if letter_char not in word or word[i] == letter_char:
                        is_still_possible = False
                        break
                else:
                    if letter_char in word:
                        is_still_possible = False
                        break

            if is_still_possible:
                new_possible_words.append(word)
        
        self.word_list = new_possible_words

    # raise NotImplementedError()

# CELL

from PIL import Image, ImageFont, ImageDraw
import random


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
        word_list: list(str) = list(
            map(lambda x: x.strip().upper(), open(word_list_file, "r").readlines())
        )
        # record the known correct positions
        known_letters: list(str) = [None, None, None, None, None]
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
            display(img)

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
        font = ImageFont.truetype("assets/roboto_font/Roboto-Bold.ttf", FONT_SIZE)

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
    
# CELL

# Tests for Bot class.

# Check if the Bot class exists
assert "Bot" in dir(), "The Bot class does not exist, did you define it?"

# CELL

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

