# -*- coding: utf-8 -*-
"""
VachanaTTS2 model

VachanaTTS2 is a Thai text-to-speech model built on VITS architecture.
It supports multiple Thai voices and is optimized for both CPU and GPU usage.

See more: https://github.com/VYNCX/VachanaTTS2
"""
import tempfile
import wave
import numpy as np
import os


class VachanaTTS:
    # Supported voice options
    SUPPORTED_VOICES = ["th_f_1", "th_m_1", "th_f_2", "th_m_2"]
    
    def __init__(self) -> None:
        """
        Initialize VachanaTTS model.
        The model will be automatically downloaded from HuggingFace on first use.
        """
        try:
            from vachanatts import TTS as VachanaTTS_TTS
            self.tts_func = VachanaTTS_TTS
        except ImportError:
            raise ImportError(
                "vachanatts is not installed. Please install it with: pip install vachanatts"
            )

    def __call__(self, text: str, speaker_idx: str = "th_f_1", return_type: str = "file", filename: str = None, **kwargs):
        """
        Generate speech from text using VachanaTTS.

        :param str text: Input text to synthesize
        :param str speaker_idx: Voice to use (th_f_1, th_m_1, th_f_2, th_m_2). Default is "th_f_1"
        :param str return_type: Return type ("file" or "waveform")
        :param str filename: Output filename for the generated audio
        :param kwargs: Additional parameters (volume, speed, noise_scale, noise_w_scale)
        :return: File path if return_type is "file", otherwise audio waveform data
        """
        # Validate speaker_idx
        if speaker_idx not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Unsupported voice '{speaker_idx}'. Supported voices are: {', '.join(self.SUPPORTED_VOICES)}"
            )
        
        # Extract additional parameters with defaults
        volume = kwargs.get('volume', 1.0)
        speed = kwargs.get('speed', 1.0)
        noise_scale = kwargs.get('noise_scale', 0.667)
        noise_w_scale = kwargs.get('noise_w_scale', 0.8)

        if return_type == "waveform":
            # For waveform return, we need to generate to a temp file then read it
            temp_filename = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
                    temp_filename = fp.name
                
                # Generate the audio file
                self.tts_func(
                    text,
                    voice=speaker_idx,
                    output=temp_filename,
                    volume=volume,
                    speed=speed,
                    noise_scale=noise_scale,
                    noise_w_scale=noise_w_scale
                )
                
                # Read the waveform from the file
                with wave.open(temp_filename, 'rb') as wav_file:
                    n_frames = wav_file.getnframes()
                    audio_data = wav_file.readframes(n_frames)
                    sample_width = wav_file.getsampwidth()
                    
                    # Convert bytes to numpy array based on sample width
                    if sample_width == 1:
                        waveform = np.frombuffer(audio_data, dtype=np.int8)
                    elif sample_width == 2:
                        waveform = np.frombuffer(audio_data, dtype=np.int16)
                    elif sample_width == 4:
                        waveform = np.frombuffer(audio_data, dtype=np.int32)
                    else:
                        raise ValueError(f"Unsupported sample width: {sample_width} bytes")
                
                return waveform
            finally:
                # Clean up temp file
                if temp_filename and os.path.exists(temp_filename):
                    os.unlink(temp_filename)
        else:
            # File output
            if filename is None:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
                    filename = fp.name
            
            self.tts_func(
                text,
                voice=speaker_idx,
                output=filename,
                volume=volume,
                speed=speed,
                noise_scale=noise_scale,
                noise_w_scale=noise_w_scale
            )
            
            return filename
