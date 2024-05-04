' test the abbreviation part of the pattern helper module '
import wetsuite.helpers.patterns

def test_form1():
    ' Test this variant of abbreviation '
    assert wetsuite.helpers.patterns.abbrev_find( "A Bree Veation (ABV)" ) == [('ABV', ['A', 'Bree', 'Veation'])]

def test_form2():
    ' Test this variant of abbreviation '
    assert wetsuite.helpers.patterns.abbrev_find( "(ABV) A Bree Veation" ) == [('ABV', ['A', 'Bree', 'Veation'])]

def test_form3():
    ' Test this variant of abbreviation '
    assert wetsuite.helpers.patterns.abbrev_find( "ABV (A Bree Veation)" ) == [('ABV', ['A', 'Bree', 'Veation'])]

def test_form4():
    ' Test this variant of abbreviation '
    assert wetsuite.helpers.patterns.abbrev_find( "(A Bree Veation) ABV" ) == [('ABV', ['A', 'Bree', 'Veation'])]

def test_count():
    ' counting of extracted abbreviations '
    parts = [
        wetsuite.helpers.patterns.abbrev_find( "A Bree Veation (ABV) and (ABV) A Bree Veation" ),
        wetsuite.helpers.patterns.abbrev_find( "ABV (A Bree Veation) and (A Bree Veation) ABV" )
    ]
    counts = wetsuite.helpers.patterns.abbrev_count_results( parts )  # counts how many documents contain it
    assert counts == {'ABV': {('A', 'Bree', 'Veation'): 2}}
