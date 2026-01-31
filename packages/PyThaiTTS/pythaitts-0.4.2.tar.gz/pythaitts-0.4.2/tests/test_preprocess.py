# -*- coding: utf-8 -*-
"""
Unit tests for Thai text preprocessing module
"""
import unittest
from pythaitts.preprocess import num_to_thai, expand_maiyamok, preprocess_text


class TestNumToThai(unittest.TestCase):
    """Test number to Thai text conversion"""
    
    def test_single_digits(self):
        """Test single digit numbers"""
        self.assertEqual(num_to_thai("0"), "ศูนย์")
        self.assertEqual(num_to_thai("1"), "หนึ่ง")
        self.assertEqual(num_to_thai("5"), "ห้า")
        self.assertEqual(num_to_thai("9"), "เก้า")
    
    def test_tens(self):
        """Test numbers 10-99"""
        self.assertEqual(num_to_thai("10"), "สิบ")
        self.assertEqual(num_to_thai("11"), "สิบเอ็ด")
        self.assertEqual(num_to_thai("15"), "สิบห้า")
        self.assertEqual(num_to_thai("20"), "ยี่สิบ")
        self.assertEqual(num_to_thai("21"), "ยี่สิบเอ็ด")
        self.assertEqual(num_to_thai("99"), "เก้าสิบเก้า")
    
    def test_hundreds(self):
        """Test numbers 100-999"""
        self.assertEqual(num_to_thai("100"), "หนึ่งร้อย")
        self.assertEqual(num_to_thai("123"), "หนึ่งร้อยยี่สิบสาม")
        self.assertEqual(num_to_thai("200"), "สองร้อย")
        self.assertEqual(num_to_thai("999"), "เก้าร้อยเก้าสิบเก้า")
    
    def test_thousands(self):
        """Test numbers 1000-9999"""
        self.assertEqual(num_to_thai("1000"), "หนึ่งพัน")
        self.assertEqual(num_to_thai("1234"), "หนึ่งพันสองร้อยสามสิบสี่")
        self.assertEqual(num_to_thai("5000"), "ห้าพัน")
    
    def test_ten_thousands(self):
        """Test numbers 10000-99999"""
        self.assertEqual(num_to_thai("10000"), "หนึ่งหมื่น")
        self.assertEqual(num_to_thai("50000"), "ห้าหมื่น")
    
    def test_negative_numbers(self):
        """Test negative numbers"""
        self.assertEqual(num_to_thai("-5"), "ลบห้า")
        self.assertEqual(num_to_thai("-123"), "ลบหนึ่งร้อยยี่สิบสาม")
    
    def test_decimal_numbers(self):
        """Test decimal numbers"""
        result = num_to_thai("12.5")
        self.assertIn("จุด", result)
        self.assertIn("สิบสอง", result)
        self.assertIn("ห้า", result)


class TestExpandMaiyamok(unittest.TestCase):
    """Test Thai repetition character (ๆ) expansion"""
    
    def test_basic_maiyamok(self):
        """Test basic mai yamok expansion"""
        self.assertEqual(expand_maiyamok("ดีๆ"), "ดีดี")
        self.assertEqual(expand_maiyamok("ช้าๆ"), "ช้าช้า")
        self.assertEqual(expand_maiyamok("คนๆ"), "คนคน")
    
    def test_no_maiyamok(self):
        """Test text without mai yamok"""
        self.assertEqual(expand_maiyamok("ภาษาไทย"), "ภาษาไทย")
        self.assertEqual(expand_maiyamok("สวัสดี"), "สวัสดี")
    
    def test_maiyamok_in_sentence(self):
        """Test mai yamok in longer sentences"""
        result = expand_maiyamok("เดินช้าๆ")
        self.assertNotIn("ๆ", result)
        self.assertIn("ช้า", result)


class TestPreprocessText(unittest.TestCase):
    """Test full text preprocessing"""
    
    def test_number_conversion(self):
        """Test number conversion in text"""
        result = preprocess_text("ฉันมี 123 บาท")
        self.assertNotIn("123", result)
        self.assertIn("หนึ่งร้อยยี่สิบสาม", result)
    
    def test_maiyamok_expansion(self):
        """Test mai yamok expansion in text"""
        result = preprocess_text("ดีๆ")
        self.assertEqual(result, "ดีดี")
    
    def test_combined_preprocessing(self):
        """Test both number conversion and mai yamok expansion"""
        result = preprocess_text("มี 5 คนๆ")
        self.assertNotIn("5", result)
        self.assertNotIn("ๆ", result)
        self.assertIn("ห้า", result)
        self.assertIn("คนคน", result)
    
    def test_no_preprocessing_numbers(self):
        """Test with number preprocessing disabled"""
        result = preprocess_text("มี 5 คน", expand_numbers=False)
        self.assertIn("5", result)
    
    def test_no_preprocessing_maiyamok(self):
        """Test with mai yamok preprocessing disabled"""
        result = preprocess_text("ดีๆ", expand_maiyamok_char=False)
        self.assertIn("ๆ", result)
    
    def test_empty_text(self):
        """Test empty text"""
        result = preprocess_text("")
        self.assertEqual(result, "")
    
    def test_text_without_preprocessing_needs(self):
        """Test text that doesn't need preprocessing"""
        text = "ภาษาไทย ง่าย มาก"
        result = preprocess_text(text)
        self.assertEqual(result, text)


if __name__ == '__main__':
    unittest.main()
