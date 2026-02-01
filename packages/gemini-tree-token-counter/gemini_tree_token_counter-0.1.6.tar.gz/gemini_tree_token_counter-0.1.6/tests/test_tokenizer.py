import pytest
from gemini_tree_token_counter.main import tokenize, get_token_count

class TestTokenizer:
    def test_tokenize_sentences(self):
        assert tokenize('Hello, world!') == ['Hello', ',', ' world', '!']
        assert tokenize("It's Monday.") == ['It', "'", 's', ' Monday', '.']

    def test_tokenize_common_abbreviations(self):
        assert tokenize('www') == ['www']
        assert tokenize('http') == ['http']
        assert tokenize('https') == ['https']

    def test_tokenize_consonant_pairs(self):
        assert tokenize('bc') == ['bc']
        assert tokenize('BC') == ['BC']

    def test_split_based_on_casing(self):
        # Camel casing
        assert tokenize('agencyStateName') == ['agency', 'State', 'Name']
        # Pascal casing
        assert tokenize('AgencyStateName') == ['Agency', 'State', 'Name']

    def test_tokenize_numbers(self):
        # Currency
        assert tokenize('$12.52') == ['$', '1', '2', '.', '5', '2']
        # Numbers
        assert tokenize('123456') == ['1', '2', '3', '4', '5', '6']

    def test_tokenize_json(self):
        json_text = '{"_index": "bid-data"}'
        tokenized_json = ['{"_', 'index', '":', ' "', 'bid', '-', 'data', '"}']
        assert tokenize(json_text) == tokenized_json

    def test_tokenize_long_words(self):
        assert tokenize('Aaaaaaaaaaa') == ['Aaaaaaaaa', 'aa']
        assert tokenize('aaaaaaaaaaa') == ['aaaaaaaaa', 'aa']
        assert tokenize('AAAAAAAAAAA') == ['AAAAAAAAA', 'AA']
        assert tokenize('bcdfgh') == ['bc', 'df', 'gh']
        assert tokenize('BCDFGH') == ['BC', 'DF', 'GH']

    def test_tokenize_repeated_special_characters(self):
        assert tokenize('------------------') == ['----------------', '--']
        assert tokenize('..................') == ['................', '..']
        assert tokenize('==================') == ['================', '==']
        assert tokenize('##################') == ['################', '##']
        assert tokenize('__________________') == ['________________', '__']
        assert tokenize('==##--') == ['==', '##', '--']

    def test_tokenize_brackets(self):
        assert tokenize('[]{}()') == ['[]', '{}', '()']

    def test_tokenize_unicode_characters(self):
        assert tokenize('©®♥') == ['©', '®', '♥']
        assert tokenize(' ') == ['', '', '', ' ', '', '', '']
        # Replacement characters
        assert tokenize('') == []

    def test_tokenize_non_latin_characters(self):
        # Ukrainian text
        text = 'використання порталу постачальників'
        expected = [
            'викор',
            'истан',
            'ня',
            ' порта',
            'лу',
            ' поста',
            'чальн',
            'иків',
        ]
        assert tokenize(text) == expected

    def test_tokenize_french_text(self):
        french_text = (
            "Bonjour le monde. C'est un très beau jour aujourd'hui. "
            "J'espère que vous allez bien. Voilà une façon différente d'écrire "
            "avec des accents et des œuvres d'art. Où est le café? À bientôt!"
        )
        expected_tokens = [
            'Bonjour', ' le', ' monde', '.', ' ', 'C', "'", 'est', ' un', ' très',
            ' beau', ' jour', ' aujourd', "'", 'hui', '.', ' ', 'J', "'", 'espère',
            ' que', ' vous', ' allez', ' bien', '.', ' Voilà', ' une', ' façon',
            ' différent', 'e', ' ', 'd', "'", 'écrire', ' avec', ' des', ' accents',
            ' et', ' des', ' œuvres', ' ', 'd', "'", 'art', '.', ' Où', ' est',
            ' le', ' café', '?', ' À', ' bientôt', '!'
        ]
        assert tokenize(french_text) == expected_tokens

    def test_tokenize_uppercase_french_text(self):
        french_text_upper = (
            "BONJOUR LE MONDE. C'EST UN TRÈS BEAU JOUR AUJOURD'HUI. "
            "J'ESPÈRE QUE VOUS ALLEZ BIEN. VOILÀ UNE FAÇON DIFFÉRENTE D'ÉCRIRE "
            "AVEC DES ACCENTS ET DES ŒUVRES D'ART. OÙ EST LE CAFÉ? À BIENTÔT!"
        )
        expected_tokens = [
            'BONJOUR', ' LE', ' MONDE', '.', ' ', 'C', "'", 'EST', ' UN', ' TRÈS',
            ' BEAU', ' JOUR', ' AUJOURD', "'", 'HUI', '.', ' ', 'J', "'", 'ESPÈRE',
            ' QUE', ' VOUS', ' ALLEZ', ' BIEN', '.', ' VOILÀ', ' UNE', ' FAÇON',
            ' DIFFÉRENT', 'E', ' ', 'D', "'", 'ÉCRIRE', ' AVEC', ' DES', ' ACCENTS',
            ' ET', ' DES', ' ŒUVRES', ' ', 'D', "'", 'ART', '.', ' OÙ', ' EST',
            ' LE', ' CAFÉ', '?', ' À', ' BIENTÔT', '!'
        ]
        assert tokenize(french_text_upper) == expected_tokens

    def test_tokenize_spanish_text(self):
        spanish_text = (
            'Hola, ¿cómo estás? El niño juega en el jardín. La señora compró manzanas. '
            'Mañana tenemos una reunión importante. El español utiliza acentos y la letra ñ. '
            '¡Qué día tan maravilloso!'
        )
        expected_tokens = [
            'Hola', ',', ' ', '¿', 'cómo', ' estás', '?', ' El', ' niño', ' juega',
            ' en', ' el', ' jardín', '.', ' La', ' señora', ' compró', ' manzanas',
            '.', ' Mañana', ' tenemos', ' una', ' reunión', ' important', 'e', '.',
            ' El', ' español', ' utiliz', 'a', ' acentos', ' y', ' la', ' letra',
            ' ', 'ñ', '.', ' ', '¡', 'Qué', ' día', ' tan', ' maravill', 'oso', '!'
        ]
        assert tokenize(spanish_text) == expected_tokens

    def test_tokenize_uppercase_spanish_text(self):
        spanish_text_upper = (
            'HOLA, ¿CÓMO ESTÁS? EL NIÑO JUEGA EN EL JARDÍN. LA SEÑORA COMPRÓ MANZANAS. '
            'MAÑANA TENEMOS UNA REUNIÓN IMPORTANTE. EL ESPAÑOL UTILIZA ACENTOS Y LA LETRA Ñ. '
            '¡QUÉ DÍA TAN MARAVILLOSO!'
        )
        expected_tokens = [
            'HOLA', ',', ' ', '¿', 'CÓMO', ' ESTÁS', '?', ' EL', ' NIÑO', ' JUEGA',
            ' EN', ' EL', ' JARDÍN', '.', ' LA', ' SEÑORA', ' COMPRÓ', ' MANZANAS',
            '.', ' MAÑANA', ' TENEMOS', ' UNA', ' REUNIÓN', ' IMPORTANT', 'E', '.',
            ' EL', ' ESPAÑOL', ' UTILIZ', 'A', ' ACENTOS', ' Y', ' LA', ' LETRA',
            ' ', 'Ñ', '.', ' ', '¡', 'QUÉ', ' DÍA', ' TAN', ' MARAVILL', 'OSO', '!'
        ]
        assert tokenize(spanish_text_upper) == expected_tokens

    def test_tokenize_german_text(self):
        german_text = (
            'Guten Tag! Wie geht es Ihnen? Ich möchte ein Stück Käse kaufen. '
            'Die Straße ist sehr lang. Über den Fluss und durch den Wald. '
            'Die schönen Äpfel schmecken süß. Das Mädchen liest ein Buch.'
        )
        expected_tokens = [
            'Guten', ' Tag', '!', ' Wie', ' geht', ' es', ' Ihnen', '?', ' Ich',
            ' möchte', ' ein', ' Stück', ' Käse', ' kaufen', '.', ' Die', ' Straße',
            ' ist', ' sehr', ' lang', '.', ' Über', ' den', ' Fluss', ' und',
            ' durch', ' den', ' Wald', '.', ' Die', ' schönen', ' Äpfel', ' ',
            'sc', 'hmecken', ' süß', '.', ' Das', ' Mädchen', ' liest', ' ein',
            ' Buch', '.'
        ]
        assert tokenize(german_text) == expected_tokens

    def test_tokenize_uppercase_german_text(self):
        german_text_upper = (
            'GUTEN TAG! WIE GEHT ES IHNEN? ICH MÖCHTE EIN STÜCK KÄSE KAUFEN. '
            'DIE STRASSE IST SEHR LANG. ÜBER DEN FLUSS UND DURCH DEN WALD. '
            'DIE SCHÖNEN ÄPFEL SCHMECKEN SÜß. DAS MÄDCHEN LIEST EIN BUCH.'
        )
        expected_tokens = [
            'GUTEN', ' TAG', '!', ' WIE', ' GEHT', ' ES', ' IHNEN', '?', ' ICH',
            ' MÖCHTE', ' EIN', ' STÜCK', ' KÄSE', ' KAUFEN', '.', ' DIE', ' STRASSE',
            ' IST', ' SEHR', ' LANG', '.', ' ÜBER', ' DEN', ' FLUSS', ' UND',
            ' DURCH', ' DEN', ' WALD', '.', ' DIE', ' SCHÖNEN', ' ÄPFEL', ' ',
            'SC', 'HMECKEN', ' SÜ', 'ß', '.', ' DAS', ' MÄDCHEN', ' LIEST',
            ' EIN', ' BUCH', '.'
        ]
        assert tokenize(german_text_upper) == expected_tokens

    def test_tokenize_mixed_multilingual_text(self):
        mixed_text = (
            "This is a mélange of différentes languages. El niño está learning German und "
            "Französisch. Schöne Bücher y señoras with œuvres d'art. Über die Straße and "
            "à travers la forêt."
        )
        expected_tokens = [
            'This', ' is', ' a', ' mélange', ' of', ' différent', 'es', ' languages',
            '.', ' El', ' niño', ' está', ' learning', ' German', ' und', ' Französis',
            'ch', '.', ' Schöne', ' Bücher', ' y', ' señoras', ' with', ' œuvres',
            ' ', 'd', "'", 'art', '.', ' Über', ' die', ' Straße', ' and', ' à',
            ' travers', ' la', ' forêt', '.'
        ]
        assert tokenize(mixed_text) == expected_tokens

    def test_preserve_all_characters(self):
        json_text = '{"_index": "bid-data"}'
        assert "".join(tokenize(json_text)) == json_text

    def test_get_token_count(self):
        text = 'Hello, world!'
        assert get_token_count(text) == 4