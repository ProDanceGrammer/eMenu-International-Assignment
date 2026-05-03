import re
import math
from typing import Tuple, List, Dict, Any
import json

import pdfplumber


MENU_PATH = 'data/espn_bet.pdf'
OUTPUT_PATH = 'output/menu_data.json'
# Pattern to match prices ($XX or $X)
PRICE_PATTERN = re.compile(r'\$\d+')

# Pattern to match price placeholder
PRICE_PLACEHOLDER_PATTERN = re.compile(r'\$X\b')

DEFAULT_MAX_LENGTH = 100_000

WHITESPACE_PIXELS_DISTANCE = 10

SHORT_NEW_LINE_PIXELS_DIFFERENCE = 10
SAME_LINE_THRESHOLD = 5

MAIN_COLUMN_LENGTH = 190
MAX_DESCRIPTION_LENGTH = 400
PAGE_PIXELS_LENGTH = 1100

class Word:
    def __init__(self, **word):
        self.price_placeholder: bool = False
        self.price_with_number: bool = False
        self._is_price: bool = False
        self.left_neighbor: Word
        self.right_neighbor: Word
        self.above_neighbor: Word
        self.below_neighbor: Word
        self.length_diff: dict = {-1: DEFAULT_MAX_LENGTH}
        self.id_in_page: int = 0
        self.included_in_phrase: bool = False
        self._phrase_id: int = 0
        self.text: str = ""
        self.top: float = None
        self.bottom: float = None
        self.x0: float = None
        self.x1: float = None
        self.height: float = None
        self.left_neighbor: Word
        self.right_neighbor: Word
        self.above_neighbor: Word
        self.below_neighbor: Word
        if word:
            self.word_dict = word
            self.text = word['text'].strip()
            self.doctop = word['doctop']
            self.top = word['top']
            self.bottom = word['bottom']
            self.x0 = word['x0']
            self.x1 = word['x1']
            self.height = word['height']
            self.left_neighbor = None
            self.right_neighbor = None
            self.above_neighbor = None
            self.below_neighbor = None

    def set_phrase_id(self, phrase_id):
        self._phrase_id = phrase_id
        self.included_in_phrase = True

    @property
    def phrase_id(self):
        return self._phrase_id

    def set_id(self, id: int):
        self.id_in_page = id

    @property
    def is_price(self):
        if len(self.text) < 5:
            # Price cannot be longer than 1 word
            is_price_with_number = bool(PRICE_PATTERN.match(self.text))
            is_price_placeholder = bool(PRICE_PLACEHOLDER_PATTERN.match(self.text))

            if is_price_with_number or is_price_placeholder:
                self.price_with_number = is_price_with_number
                self.price_placeholder = is_price_placeholder
                self._is_price = True

        return self._is_price

class Phrase:
    def __init__(self, word: Word = Word(), phrase_id: int = -1):
        self.words: List[Word] = [word]
        self.id: int = phrase_id
        self.type: str = 'default' # other types are 'item', 'potential_item', 'category', 'subcategory', 'subitem', 'price', 'description'
        self.price_placeholder: bool = False
        self.price_with_number: bool = False
        self.description_phrase = None
        self.category_phrase = None
        self.category_distance: float = DEFAULT_MAX_LENGTH
        self.sub_category_phrase = None
        self.sub_category_vertical_distance: float = DEFAULT_MAX_LENGTH
        self.price_phrase = None
        # TODO: Replace typing with composition

        if phrase_id != -1:
            self.description_phrase: Phrase = Phrase()
            self.category_phrase: Phrase = Phrase()
            self.sub_category_phrase: Phrase = Phrase()
            self.price_phrase: Phrase = Phrase()

    def __repr__(self):
        return self.text
    
    def decoding(self, text):
        decoded_text = text.replace('\u2019', "'").replace('\u2026', '...').replace('\u201c', '"').replace(
            '\u201d', '"').replace('\u00f1', 'n').replace('\u00e0', 'a').replace('\u00f3', 'o')
        return decoded_text

    @property
    def text(self):
        return self.decoding(" ".join([word.text for word in self.words]))

    @property
    def price_format(self):
        output = self.text
        if len(self.text) == 0 or self.price_placeholder:
            output = None
        return output

    @property
    def x0(self) -> float:
        return self.words[0].x0

    @property
    def x1(self) -> float:
        return self.words[-1].x1

    def extend(self, word: Word):
        word.set_phrase_id(self.id)
        self.words.append(word)

    @property
    def min_height(self) -> float:
        return min([word.height for word in self.words])

    @property
    def max_height(self) -> float:
        return max([word.height for word in self.words])

    @property
    def height_range(self) -> Tuple[float, float]:
        return self.min_height, self.max_height

    @property
    def min_y(self) -> float:
        return PAGE_PIXELS_LENGTH - max([word.doctop for word in self.words])

    @property
    def max_y(self) -> float:
        return PAGE_PIXELS_LENGTH - min([word.doctop for word in self.words])

    def update_price_state(self):
        if len(self.words) == 1:
            # Price cannot be longer than 1 word
            is_price_with_number = bool(PRICE_PATTERN.match(self.words[0].text))
            is_price_placeholder = bool(PRICE_PLACEHOLDER_PATTERN.match(self.words[0].text))

            if is_price_with_number or is_price_placeholder:
                self.type = 'price'
                self.price_with_number = is_price_with_number
                self.price_placeholder = is_price_placeholder

    def classify(self, **types_data):
        if self.max_height == types_data['category_size']:
            self.type = 'category'

        self.update_price_state()

def structure_page(pdf_path, page_num=0):

    def preprocess_words(words: List[Dict[str, Any]]) -> List[Word]:

        preprocessed_words = []
        for i, word_dict in enumerate(words):
            word = Word(**word_dict)

            word.set_id(i)

            preprocessed_words.append(word)

        return preprocessed_words

    def update_neighbors_data(words: List[Word]) -> List[Word]:
        updated_words = []
        # Collect information about neighbor words
        for i, word in enumerate(words):
            word.left_neighbor = Word()
            word.right_neighbor = Word()
            word.above_neighbor = Word()
            word.below_neighbor = Word()

            for j, neighbor_word in enumerate(words):
                # Exclude same word
                if i == j:
                    continue
                # Check if the neighbor word is to the right from a target word

                # Horizontally neighbor word
                if abs(word.top - neighbor_word.top) < SAME_LINE_THRESHOLD:
                    left_diff = word.x0 - neighbor_word.x1  # from target word to left neighbor word
                    right_diff = neighbor_word.x0 - word.x1  # from target word to right neighbor word

                    # Compare with a neighbor set before
                    if 0 < right_diff < word.right_neighbor.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH):
                        words[j].length_diff.update({
                            word.id_in_page: right_diff
                        })
                        word.right_neighbor = words[j]

                    elif 0 < left_diff < word.left_neighbor.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH):
                        words[j].length_diff.update({
                            word.id_in_page: left_diff
                        })
                        word.left_neighbor = words[j]

                # Vertically neighbor word
                else:
                    # Positive vertical_diff means the neighbor word is below target word
                    vertical_diff = neighbor_word.top - word.top   # from target word to neighbor word vertically

                    if 0 < vertical_diff < word.below_neighbor.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH):
                        words[j].length_diff.update({
                            word.id_in_page: vertical_diff
                        })
                        word.below_neighbor = words[j]

                    elif vertical_diff < 0 and abs(vertical_diff) < word.above_neighbor.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH):
                        words[j].length_diff.update({
                            word.id_in_page: abs(vertical_diff)
                        })
                        word.above_neighbor = words[j]
                    else:
                        words[j].length_diff.update({
                            word.id_in_page: abs(vertical_diff)
                        })

            updated_words.append(word)
        return updated_words

    def obtain_sizes_data(words) -> Dict[str, float]:

        font_sizes = {}

        for word in words:
            if word.height not in font_sizes.keys():
                font_sizes.update({
                    word.height: 0
                })
            else:
                # Increment frequentness
                current_frequentness = font_sizes[word.height]

                font_sizes.update({
                    word.height: current_frequentness + 1
                })

        all_font_sizes = list(font_sizes.keys())
        all_font_sizes.sort()
        category_size = max(all_font_sizes)
        sizes_data = {
            'category_size': category_size,
            'subcategory_size': all_font_sizes[-2]
        }
        return sizes_data

    def obtain_phrases(words: List[Word]) -> List[Phrase]:
        def next_word_close(word: Word, phrase: Phrase) -> Tuple[Word, bool]:
            next_word = word.right_neighbor
            if next_word.is_price:
                return next_word, False

            is_right_neighbor_close = next_word.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH) < WHITESPACE_PIXELS_DISTANCE
            is_neighbor_straight_below_and_close = False

            if not is_right_neighbor_close:

                if word.below_neighbor.is_price:
                    below_price = word.below_neighbor
                    word.below_neighbor = below_price.below_neighbor # word under price, which is next word, becomes below word of current word
                    below_price.below_neighbor = word.below_neighbor

                next_word = word.below_neighbor
                if next_word.x0 is not None:

                    is_neighbor_straight_below = abs(next_word.x0 - phrase.x0) < SAME_LINE_THRESHOLD
                    is_below_neighbor_close = next_word.length_diff.get(word.id_in_page, DEFAULT_MAX_LENGTH) < SHORT_NEW_LINE_PIXELS_DIFFERENCE

                    is_neighbor_straight_below_and_close = is_neighbor_straight_below and is_below_neighbor_close


            is_next_neighbor_close = is_right_neighbor_close or is_neighbor_straight_below_and_close

            return next_word, is_next_neighbor_close

        # Set of ids which are already in phrases
        phrases: List[Phrase] = []
        phrase_id = 0

        for word in words:
            if word.included_in_phrase:
                continue

            phrase = Phrase(word, phrase_id)

            next_word, is_next_neighbor_close = next_word_close(word, phrase)

            while is_next_neighbor_close:
                phrase.extend(next_word)
                next_word, is_next_neighbor_close = next_word_close(next_word, phrase)

            phrases.append(phrase)

            phrase_id += 1

        return phrases

    def euclidean_distance(x1, x2, y1, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def phrases_processing(phrases: List[Phrase], size_data: Dict[str, float]) -> List[Dict[str, Any]]:

        def phrases_classify(phrases: List[Phrase]):
            for i, phrase in enumerate(phrases):
                phrase.classify(**size_data)
            return phrases

        def accumulate_categories(phrases: List[Phrase]) -> set[Phrase]:
            category_phrases: set[Phrase] = set()
            for i, phrase in enumerate(phrases):
                if phrase.type == 'category':
                    category_phrases.add(phrase)
            return category_phrases

        def accumulate_potential_items(phrases: List[Phrase], category_phrases) -> List[Phrase]:
            item_phrases: List[Phrase] = []
            # Traverse potential items by categories
            for i, category_phrase in enumerate(category_phrases):
                # Traverse subphrases
                for potential_item_phrase in phrases:
                    if potential_item_phrase.type in ['category', 'price']:
                        continue
                    if potential_item_phrase.max_height >= category_phrase.max_height:
                        continue
                    if potential_item_phrase.max_y > category_phrase.min_y:
                        continue
                    if potential_item_phrase.x0 < category_phrase.x0:
                        continue
                    if not potential_item_phrase.text.isupper():
                        continue
                    # TODO: exclude the coupling with a uppercase logic, because in other menu it will look differently

                    # is this phrase an item of this category
                    # Is a sub-phrase below this Category

                    distance_with_current_category = euclidean_distance(potential_item_phrase.x0, category_phrase.x0,
                                                                        potential_item_phrase.min_y,
                                                                        category_phrase.min_y)

                    # Is a sub-phrase in any other categories
                    other_category_sub_phrase = False
                    for another_category in category_phrases:
                        if another_category.id == category_phrase.id:
                            continue

                        distance_with_another_category = euclidean_distance(potential_item_phrase.x0,
                                                                            another_category.x0,
                                                                            potential_item_phrase.min_y,
                                                                            another_category.min_y)
                        if 0 <= potential_item_phrase.x0 - another_category.x0 < MAIN_COLUMN_LENGTH:
                            if potential_item_phrase.max_y < another_category.min_y:
                                if distance_with_another_category < distance_with_current_category:
                                    other_category_sub_phrase = True
                                    break

                    if other_category_sub_phrase:
                        continue

                    potential_item_phrase.category_phrase = category_phrase
                    potential_item_phrase.category_distance = distance_with_current_category
                    item_phrases.append(potential_item_phrase)

            return item_phrases

        def allocate_descriptions(phrases: List[Phrase], item_phrases):

            # traverse to find description
            for item_phrase in item_phrases:
                for potential_description_phrase in phrases:
                    if potential_description_phrase.id == item_phrase.id:
                        continue

                    if potential_description_phrase.type in ['category', 'price']:
                        continue

                    if potential_description_phrase.max_height >= item_phrase.max_height:
                        continue

                    if potential_description_phrase.max_y > item_phrase.min_y:
                        continue

                    if abs(potential_description_phrase.x1 - potential_description_phrase.x0) > MAX_DESCRIPTION_LENGTH:
                        continue

                    distance_with_current_item = euclidean_distance(potential_description_phrase.x0, item_phrase.x0,
                                                                    potential_description_phrase.min_y,
                                                                    item_phrase.min_y)

                    # Is a sub-phrase in any other categories
                    other_item_description = False
                    for another_item_phrase in item_phrases:
                        if another_item_phrase.id == item_phrase.id:
                            continue

                        distance_with_another_item = euclidean_distance(potential_description_phrase.x0,
                                                                        another_item_phrase.x0,
                                                                        potential_description_phrase.min_y,
                                                                        another_item_phrase.min_y)

                        if potential_description_phrase.max_y < another_item_phrase.min_y or 0 < abs(
                                potential_description_phrase.x0 - another_item_phrase.x0) < MAIN_COLUMN_LENGTH:
                            if distance_with_another_item < distance_with_current_item:
                                other_item_description = True
                                break

                    if other_item_description:
                        continue

                    item_phrase.description_phrase = potential_description_phrase
                    potential_description_phrase.type = 'description'
                    break

            return phrases, item_phrases

        def allocate_prices(item_phrases, phrases, category_phrases):
            # Traverse to find prices
            for i, item_phrase in enumerate(item_phrases + list(category_phrases)):
                for potential_price_phrase in phrases:

                    if potential_price_phrase.type not in ['price']:
                        continue
                    if abs(potential_price_phrase.max_y - item_phrase.max_y) > 5:
                        continue

                    if potential_price_phrase.x0 < item_phrase.x0:
                        continue

                    if item_phrase.words[-1].right_neighbor.id_in_page is not potential_price_phrase.words[
                        0].id_in_page:
                        continue

                    item_phrase.price_phrase = potential_price_phrase
            return item_phrases, phrases, category_phrases

        def accumulate_subcategories(item_phrases):
            subcategory_phrases: set[Phrase] = set()
            # Traverse subcategories
            for i, item_phrase in enumerate(item_phrases):
                # TODO: Replace with is_instance(item_phrase, PricePhrase)
                if item_phrase.max_height == size_data['subcategory_size']:
                    item_phrase.type = "subcategory"

                # if item does not have price and size is greater or equal to the biggest
                elif item_phrase.price_phrase.type == 'default' and item_phrase.max_height <= size_data[
                    'category_size']:
                    item_phrase.type = "potential_subcategory"
                else:
                    continue

                subcategory_phrases.add(item_phrase)
            return item_phrases, subcategory_phrases

        def accumulate_subitems(item_phrases, subcategory_phrases):

            subitem_phrases: set[Phrase] = set()
            for i, subcategory_phrase in enumerate(subcategory_phrases):
                for potential_sub_item_phrase in item_phrases:
                    # TODO add sorting in result by category and items' coordinates
                    if potential_sub_item_phrase.id is subcategory_phrase.id:
                        continue
                    if potential_sub_item_phrase.type in ['subcategory']:
                        continue
                    if subcategory_phrase.type in ['subitem']:
                        continue
                    if subcategory_phrase.type == potential_sub_item_phrase.type == 'potential_subcategory':
                        continue
                    if potential_sub_item_phrase.max_height > subcategory_phrase.max_height:
                        continue
                    if potential_sub_item_phrase.max_y > subcategory_phrase.min_y:
                        continue
                    if potential_sub_item_phrase.x0 < subcategory_phrase.x0:
                        continue
                    if not potential_sub_item_phrase.text.isupper():
                        continue
                    # TODO: exclude the coupling with a uppercase logic, because in other menu it will look differently

                    # Is a sub-phrase below this subcategory
                    distance_with_current_subcategory = euclidean_distance(potential_sub_item_phrase.x0,
                                                                           subcategory_phrase.x0,
                                                                           potential_sub_item_phrase.min_y,
                                                                           subcategory_phrase.min_y)
                    vertical_distance_current_subcategory = subcategory_phrase.min_y - potential_sub_item_phrase.min_y

                    # Is a sub-phrase in any other categories
                    other_category_sub_phrase = False
                    for another_subcategory in subcategory_phrases.union(category_phrases):
                        if another_subcategory.id == subcategory_phrase.id or another_subcategory.type == 'subitem':
                            continue

                        distance_with_another_subcategory = euclidean_distance(potential_sub_item_phrase.x0,
                                                                               another_subcategory.x0,
                                                                               potential_sub_item_phrase.min_y,
                                                                               another_subcategory.min_y)
                        vertical_distance_another_subcategory = another_subcategory.min_y - potential_sub_item_phrase.min_y

                        # is to the down from alternative subcategory
                        if (potential_sub_item_phrase.max_y < another_subcategory.min_y
                                and vertical_distance_current_subcategory >= vertical_distance_another_subcategory):
                            if 0 <= potential_sub_item_phrase.x0 - another_subcategory.x0 < MAIN_COLUMN_LENGTH:
                                if distance_with_another_subcategory < distance_with_current_subcategory:
                                    other_category_sub_phrase = True
                                    break

                    if other_category_sub_phrase:
                        continue

                    if potential_sub_item_phrase.sub_category_vertical_distance < vertical_distance_current_subcategory:
                        continue
                    if potential_sub_item_phrase.category_distance < distance_with_current_subcategory:
                        continue

                    potential_sub_item_phrase.sub_category_vertical_distance = vertical_distance_current_subcategory
                    potential_sub_item_phrase.sub_category_phrase = subcategory_phrase
                    potential_sub_item_phrase.type = "subitem"

                    subitem_phrases.add(potential_sub_item_phrase)

            return subitem_phrases, item_phrases, subcategory_phrases

        def format_output(item_phrases, subitem_phrases):
            result_json = []
            # Excluding 'descriptions', 'category', 'price','subcategory', 'subitem' from items
            for i, item_phrase in enumerate(item_phrases):

                # Pull a price from a category if in item it is excluded
                if item_phrase.price_phrase.type != 'price' and item_phrase.category_phrase.price_phrase.type == 'price':
                    item_phrase.price_phrase = item_phrase.category_phrase.price_phrase
                    item_phrase.type = "item"

                if item_phrase.type in ['description', 'category', 'price', 'subcategory', 'potential_subcategory',
                                        'subitem']:
                    continue

                result_json.append({
                    "phrase": item_phrase,
                    "category": item_phrase.category_phrase.text,
                    "dish_name": item_phrase.text,
                    "price": item_phrase.price_phrase.price_format,
                    "description": item_phrase.description_phrase.text,
                    "dish_id": item_phrase.id
                })

            for i, subitem_phrase in enumerate(subitem_phrases):

                if subitem_phrase.type not in ['subitem']:
                    continue

                result_json.append({
                    "phrase": subitem_phrase,
                    "category": subitem_phrase.category_phrase.text,
                    "dish_name": f"{subitem_phrase.sub_category_phrase.text} ({subitem_phrase.text})",
                    "price": subitem_phrase.price_phrase.price_format,
                    "description": subitem_phrase.description_phrase.text,
                    "dish_id": subitem_phrase.id
                })
            return result_json

        phrases = phrases_classify(phrases)

        category_phrases = accumulate_categories(phrases)

        item_phrases = accumulate_potential_items(phrases, category_phrases)

        phrases, item_phrases = allocate_descriptions(phrases, item_phrases)

        item_phrases, phrases, category_phrases = allocate_prices(item_phrases, phrases, category_phrases)

        item_phrases, subcategory_phrases = accumulate_subcategories(item_phrases)

        subitem_phrases, item_phrases, subcategory_phrases = accumulate_subitems(item_phrases, subcategory_phrases)

        result_json = format_output(item_phrases, subitem_phrases)

        return result_json

    def order_output(result_json) -> List[Dict[str, Any]]:

        ordered_output = result_json.copy()
        # Order by category and item coordinates
        ordered_output.sort(key=lambda item: item["phrase"].category_phrase.min_y, reverse=True)
        ordered_output.sort(key=lambda item: item["phrase"].category_phrase.x0)
        ordered_output.sort(key=lambda item: item["phrase"].min_y, reverse=True)
        ordered_output.sort(key=lambda item: item["phrase"].x0)
        # TODO: Upgrade sorting with subcategories
        return ordered_output

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # Get all words with their bounding boxes
        parsed_words = page.extract_words()

    # Build result with character-level coordinates
    parsed_words.sort(key=lambda word: word['top'])

    # Preprocess (update price data)
    words = preprocess_words(parsed_words)

    words = update_neighbors_data(words)

    sizes_data = obtain_sizes_data(words)

    phrases = obtain_phrases(words)

    result_json = phrases_processing(phrases, sizes_data)

    result_json = order_output(result_json)

    return result_json


if __name__ == "__main__":
    ordered_output = []

    # Iterate on pages
    for i in range(2):
        ordered_output.extend(structure_page(MENU_PATH, page_num=i))

    # Order whole data
    for i, item in enumerate(ordered_output):
        item['dish_id'] = i
        item.pop("phrase")

    # Writing to a file
    with open(OUTPUT_PATH, "w") as f:
        json.dump(ordered_output, f, indent=4)
