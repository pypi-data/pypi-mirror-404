# -*- coding: utf-8 -*-
"""
Thai Text Preprocessing for TTS

This module provides text preprocessing functions for Thai Text-to-Speech,
including number to Thai text conversion and handling of Thai repetition character (ๆ).
"""
import re


# Thai number words
THAI_ONES = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
THAI_TENS = ["", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ"]


def _num_to_thai_under_hundred(num: int) -> str:
    """
    Convert numbers 0-99 to Thai text.
    
    :param int num: Number to convert (0-99)
    :return: Thai text representation
    :rtype: str
    """
    if num == 0:
        return "ศูนย์"
    elif num < 10:
        return THAI_ONES[num]
    elif num < 20:
        if num == 10:
            return "สิบ"
        elif num == 11:
            return "สิบเอ็ด"
        else:
            return "สิบ" + THAI_ONES[num % 10]
    elif num < 100:
        tens = num // 10
        ones = num % 10
        result = THAI_TENS[tens]
        if ones == 1:
            result += "เอ็ด"
        elif ones > 1:
            result += THAI_ONES[ones]
        return result
    return ""


def _num_to_thai_under_thousand(num: int) -> str:
    """
    Convert numbers 0-999 to Thai text.
    
    :param int num: Number to convert (0-999)
    :return: Thai text representation
    :rtype: str
    """
    if num < 100:
        return _num_to_thai_under_hundred(num)
    
    hundreds = num // 100
    remainder = num % 100
    
    if hundreds == 1:
        result = "หนึ่งร้อย"
    elif hundreds == 2:
        result = "สองร้อย"
    else:
        result = THAI_ONES[hundreds] + "ร้อย"
    
    if remainder > 0:
        result += _num_to_thai_under_hundred(remainder)
    
    return result


def num_to_thai(num_str: str) -> str:
    """
    Convert number string to Thai text.
    Supports integers and decimals.
    
    :param str num_str: Number string to convert (e.g., "123", "1234", "12.5")
    :return: Thai text representation
    :rtype: str
    
    Examples:
        >>> num_to_thai("0")
        'ศูนย์'
        >>> num_to_thai("123")
        'หนึ่งร้อยยี่สิบสาม'
        >>> num_to_thai("1000")
        'หนึ่งพัน'
    """
    # Handle decimal numbers
    if '.' in num_str:
        integer_part, decimal_part = num_str.split('.')
        result = num_to_thai(integer_part) + "จุด"
        for digit in decimal_part:
            result += THAI_ONES[int(digit)] if int(digit) > 0 else "ศูนย์"
        return result
    
    # Convert to integer
    try:
        num = int(num_str)
    except ValueError:
        return num_str  # Return original if cannot convert
    
    if num == 0:
        return "ศูนย์"
    
    if num < 0:
        return "ลบ" + num_to_thai(str(-num))
    
    # Handle numbers by magnitude
    if num < 1000:
        return _num_to_thai_under_thousand(num)
    elif num < 10000:
        thousands = num // 1000
        remainder = num % 1000
        result = THAI_ONES[thousands] + "พัน"
        if remainder > 0:
            result += _num_to_thai_under_thousand(remainder)
        return result
    elif num < 100000:
        ten_thousands = num // 10000
        remainder = num % 10000
        if ten_thousands == 1:
            result = "หนึ่งหมื่น"
        elif ten_thousands == 2:
            result = "สองหมื่น"
        else:
            result = THAI_ONES[ten_thousands] + "หมื่น"
        if remainder > 0:
            thousands = remainder // 1000
            if thousands > 0:
                result += THAI_ONES[thousands] + "พัน"
            remainder = remainder % 1000
            if remainder > 0:
                result += _num_to_thai_under_thousand(remainder)
        return result
    elif num < 1000000:
        hundred_thousands = num // 100000
        remainder = num % 100000
        result = THAI_ONES[hundred_thousands] + "แสน"
        if remainder > 0:
            ten_thousands = remainder // 10000
            if ten_thousands > 0:
                result += THAI_ONES[ten_thousands] + "หมื่น"
            remainder = remainder % 10000
            thousands = remainder // 1000
            if thousands > 0:
                result += THAI_ONES[thousands] + "พัน"
            remainder = remainder % 1000
            if remainder > 0:
                result += _num_to_thai_under_thousand(remainder)
        return result
    elif num < 10000000:
        millions = num // 1000000
        remainder = num % 1000000
        result = THAI_ONES[millions] + "ล้าน"
        if remainder > 0:
            result += num_to_thai(str(remainder))
        return result
    else:
        # For very large numbers, use a simple approach
        millions = num // 1000000
        remainder = num % 1000000
        result = num_to_thai(str(millions)) + "ล้าน"
        if remainder > 0:
            result += num_to_thai(str(remainder))
        return result


def expand_maiyamok(text: str) -> str:
    """
    Expand Thai repetition character (ๆ) by repeating the previous word or syllable.
    
    The mai yamok (ๆ) is a Thai repetition mark that indicates the previous 
    word or syllable should be repeated.
    
    :param str text: Text containing ๆ character
    :return: Text with ๆ expanded
    :rtype: str
    
    Examples:
        >>> expand_maiyamok("ช้าๆ")
        'ช้าช้า'
        >>> expand_maiyamok("ดีๆ")
        'ดีดี'
    """
    if 'ๆ' not in text:
        return text
    
    result = []
    i = 0
    while i < len(text):
        if text[i] == 'ๆ':
            # Find the previous word/syllable to repeat
            if result:
                # Look back to find the word to repeat
                # Thai words are typically separated by spaces or are continuous
                # We'll repeat the last word or syllable
                prev_text = ''.join(result)
                
                # Find the last word (sequence of Thai characters)
                thai_char_pattern = r'[ก-๙]+'
                matches = list(re.finditer(thai_char_pattern, prev_text))
                if matches:
                    last_match = matches[-1]
                    word_to_repeat = last_match.group()
                    result.append(word_to_repeat)
                else:
                    # If no Thai characters found, just skip the ๆ
                    pass
            i += 1
        else:
            result.append(text[i])
            i += 1
    
    return ''.join(result)


def preprocess_text(text: str, expand_numbers: bool = True, expand_maiyamok_char: bool = True) -> str:
    """
    Preprocess Thai text for TTS by converting numbers to text and expanding ๆ.
    
    :param str text: Input text to preprocess
    :param bool expand_numbers: Whether to convert numbers to Thai text (default: True)
    :param bool expand_maiyamok_char: Whether to expand ๆ character (default: True)
    :return: Preprocessed text
    :rtype: str
    
    Examples:
        >>> preprocess_text("ฉันมี 123 บาท")
        'ฉันมี หนึ่งร้อยยี่สิบสาม บาท'
        >>> preprocess_text("ดีๆ")
        'ดีดี'
        >>> preprocess_text("มี 5 คนๆ")
        'มี ห้า คนคน'
    """
    result = text
    
    # Expand mai yamok (ๆ) first
    if expand_maiyamok_char:
        result = expand_maiyamok(result)
    
    # Convert numbers to Thai text
    if expand_numbers:
        # Find all numbers in the text and replace them
        def replace_number(match):
            return num_to_thai(match.group())
        
        # Match integers and decimals, including optional negative sign
        # Handles: -5, 123, 123.45
        result = re.sub(r'-?\d+(?:\.\d+)?', replace_number, result)
    
    return result
