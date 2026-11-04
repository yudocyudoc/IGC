"""Checks for exploratory WEBA vibration segmenter. Fixtures have no drink labels."""
import hashlib
import math
import tempfile
import unittest

from scripts.arena_cafe import weba_three_shift_vibration_exploratory as mod


class VibrationPilotTests(unittest.TestCase):
    def test_git_sha1_uses_actual_git_blob_digest(self):
        raw=b"hello\n"
        expected=hashlib.sha1(b"blob 6\0hello\n").hexdigest()
        self.assertEqual(mod.blob_sha1(raw),expected)

    def test_clock_as_seconds_and_bounds(self):
        self.assertAlmostEqual(mod.seconds_of_day("14:18:39.5000"),
                               14*3600+18*60+39.5)
        with self.assertRaises(ValueError):
            mod.seconds_of_day("24:00:00")

    def make_rows(self, t0, n, step=0.04, offset=0.0):
        h=int(t0//3600);m=int((t0%3600)//60)
        base=t0%60
        return b"".join(
            f"{h:02}:{m:02}:{base+i*step:07.4f},"
            f"{0.1*math.sin(i*0.2)+offset:.4f},"
            f"{-9.8+0.1*math.sin(i*0.3):.4f},"
            f"{0.2*math.sin(i*0.1):.4f}\n".encode()
            for i in range(n))

    def test_valid_full_five_second_window(self):
        raw=self.make_rows(12*3600,120)
        windows,qc=mod.windows_of_file(raw,0)
        self.assertEqual(qc["rows_parsed"],120)
        self.assertEqual(qc["rows_rejected"],0)
        self.assertEqual(len(windows),1)
        self.assertGreater(windows[0]["rms"],0)

    def test_short_incomplete_window_dropped(self):
        windows,qc=mod.windows_of_file(self.make_rows(12*3600,40),0)
        self.assertEqual(len(windows),0)
        self.assertEqual(qc["partial_windows_dropped"],1)

    def test_gap_is_not_filled_as_inactive(self):
        raw=self.make_rows(12*3600,120)+self.make_rows(
            12*3600+20,120)
        windows,qc=mod.windows_of_file(raw,0)
        self.assertEqual(len(windows),2)
        self.assertEqual(qc["acquisition_gaps_gt_0_3s"],1)
        self.assertNotEqual(windows[0]["run"],windows[1]["run"])

    def test_malformed_text_row_not_silently_mapped_to_label(self):
        raw=(self.make_rows(12*3600,120)+
             b"latte, 1,2,3,4\n"+
             self.make_rows(12*3600+5,120))
        _,qc=mod.windows_of_file(raw,0)
        self.assertEqual(qc["rows_rejected"],1)

    def test_episode_count_no_join_across_different_files(self):
        ws=[
            {"file_index":0,"run":0,"bin":10},
            {"file_index":0,"run":0,"bin":11},
            {"file_index":1,"run":0,"bin":12},
            {"file_index":1,"run":0,"bin":13},
        ]
        self.assertEqual(mod.episode_lengths(ws,[True]*4),[10,10])

    def test_episode_count_no_join_across_time_gap(self):
        ws=[{"file_index":0,"run":0,"bin":10},
            {"file_index":0,"run":0,"bin":12}]
        self.assertEqual(mod.episode_lengths(ws,[True,True]),[5,5])

    def test_same_file_consecutive_windows(self):
        ws=[{"file_index":0,"run":0,"bin":10},
            {"file_index":0,"run":0,"bin":11},
            {"file_index":0,"run":0,"bin":12}]
        self.assertEqual(mod.episode_lengths(ws,[True,True,True]),[15])

    def test_robust_scale_computable(self):
        self.assertAlmostEqual(mod.scaled_mad([1,1,2,3,100]),1.4826)
        self.assertEqual(mod.quantile([0,10,20],0.5),10)

    def test_sources_are_exactly_three_shifts_and_12_pinned_files(self):
        self.assertEqual(len(mod.SOURCES),12)
        self.assertEqual({x[0] for x in mod.SOURCES},
                         set(mod.TRAIN+(mod.HOLDOUT,)))
        self.assertTrue(all(len(x[3])==40 for x in mod.SOURCES))

    def test_machine_cycle_never_inferable_from_unsigned_windows(self):
        self.assertNotEqual(mod.HOLDOUT, mod.TRAIN[0])
        self.assertNotEqual(mod.HOLDOUT, mod.TRAIN[1])


if __name__=="__main__":
    unittest.main()
