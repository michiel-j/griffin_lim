

import argparse
from pylab import *
import os

import audio_utilities

# Author: Brian K. Vogel
# brian.vogel@gmail.com

def run_demo():
    """Test Griffin & Lim method for reconstructing audio from a magnitude spectrogram.

        Example of using the Griffin-Lim algorithm. The input file is loaded, the
        spectrogram is computed (note that we discard the phase information). Then,
        using only the (magnitude) spectrogram, the Griffin-Lim algorithm is run
        to reconstruct an audio signal from the spectrogram. The reconstructed audio
        is finally saved to a file.

        A plot of the spectrogram is also displayed.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_file', type=str, default="bkvhi.wav",
                        help='Input WAV file')
    parser.add_argument('--sample_rate_hz', default=44100, type=int,
                        help='Sample rate in Hz')
    parser.add_argument('--fft_size', default=2048, type=int,
                        help='FFT siz')
    parser.add_argument('--iterations', default=300, type=int,
                        help='Number of iterations to run')
    parser.add_argument('--enable_filter', action='store_true',
                        help='Apply a low-pass filter')
    parser.add_argument('--cutoff_freq', type=int, default=1000,
                        help='If filter is enable, the low-pass cutoff frequency in Hz')
    args = parser.parse_args()

    in_file = args.in_file

    # Load an audio file. It must be WAV format. Multi-channel files will be
    # converted to mono.
    input_signal = audio_utilities.get_signal(in_file, expected_fs=args.sample_rate_hz)

    # Hopsamp is the number of samples that the analysis window is shifted after
    # computing the FFT. For example, if the sample rate is 44100 Hz and hopsamp is
    # 256, then there will be approximately 44100/256 = 172 FFTs computed per second
    # and thus 172 spectral slices (i.e., columns) per second in the spectrogram.
    hopsamp = args.fft_size // 8

    # Compute the Short-Time Fourier Transform (STFT) from the audio file. This is a 2-dim Numpy array with
    # time_slices rows and frequency_bins columns. Thus, you will need to take the
    # transpose of this matrix to get the usual STFT which has frequency bins as rows
    # and time slices as columns.
    stft_full = audio_utilities.stft_for_reconstruction(input_signal,
                                                        args.fft_size, hopsamp)
    # Note that the STFT is complex-valued. Therefore, to get the (magnitude)
    # spectrogram, we need to take the absolute value.
    stft_mag = abs(stft_full)
    # Note that `stft_mag` only contains the magnitudes and so we have lost the
    # phase information.
    scale = 1.0 / np.amax(stft_mag)
    print('Maximum value in the magnitude spectrogram: ', 1/scale)
    # Rescale to put all values in the range [0, 1].
    stft_mag *= scale
    # We now have a (magnitude only) spectrogram, `stft_mag` that is normalized to be within [0, 1.0].
    # In a practical use case, we would probably want to perform some processing on `stft_mag` here
    # which would produce a modified version that we would want to reconstruct audio from.

    stft_modified = stft_mag[:]


    ###### Optional: modify the spectrogram
    # For example, we can implement a low-pass filter by simply setting all frequency bins above
    # some threshold frequency (args.cutoff_freq) to 0 as follows.
    if args.enable_filter:
        # Calculate corresponding bin index.
        cutoff_bin = round(args.cutoff_freq*args.fft_size/args.sample_rate_hz)
        stft_modified[:, cutoff_bin:] = 0
    ###########

    # Undo the rescaling.
    stft_modified_scaled = stft_modified / scale
    # Use the Griffin&Lim algorithm to reconstruct an audio signal from the
    # magnitude spectrogram.
    x_reconstruct = audio_utilities.reconstruct_signal_griffin_lim(stft_modified_scaled,
                                                                   args.fft_size, hopsamp,
                                                                   args.iterations)

    # The output signal must be in the range [-1, 1], otherwise we need to clip or normalize.
    max_sample = np.max(abs(x_reconstruct))
    if max_sample > 1.0:
        x_reconstruct = x_reconstruct / max_sample

    # Save the reconstructed signal to a WAV file.
    audio_utilities.save_audio_to_file(x_reconstruct, args.sample_rate_hz)

    # Save the spectrogram image also.
    figure(1)
    imshow(stft_modified.T ** 0.25, origin='lower', cmap=cm.hot, aspect='auto',
           interpolation='nearest')
    colorbar()
    savefig('spectrogram_figure.png', dpi=150)


if __name__ == '__main__':
    run_demo()