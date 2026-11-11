"""Pruebas del comparador; fixtures sintéticos, no acuerdos reales."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"arena_cafe"/"comparar_doble_anotacion_v0_1.py"
spec=importlib.util.spec_from_file_location("arena_comparador",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sample(event_id,time,level="OBSERVADO",code="objeto_visible_en_region"):
    return {"event_id":event_id,"event_code":code,
      "region_id":"barra_frontal_vista_principal","kind":"estado",
      "claim_level":level,"time":{"mode":"sample","samples_video_s":[time]}}

class DoubleAnnotationComparerTests(unittest.TestCase):
    def test_no_events_not_perfect(self):
        r=m.match_events([],[])
        self.assertIsNone(r["f1_symmetric"])
        self.assertTrue(r["f1_undefined_if_no_events"])

    def test_two_to_one_is_not_two_matches(self):
        a=[sample("a1",2350),sample("a2",2352)]
        b=[sample("b1",2352)]
        r=m.match_events(a,b)
        self.assertEqual(r["paired"],1)
        self.assertAlmostEqual(r["f1_symmetric"],2/3)

    def test_unknown_is_not_positive(self):
        r=m.match_events([sample("a",2350,level="DESCONOCIDO")],[sample("b",2350)])
        self.assertEqual(r["paired"],0)
        self.assertEqual(r["unknown_a"],1)

    def test_two_second_limit(self):
        self.assertEqual(m.event_distance(sample("a",2350),sample("b",2352)),2)
        self.assertEqual(m.event_distance(sample("a",2350),sample("b",2354)),4)

    def test_transition_overlap(self):
        a={"event_code":"objeto_aparece_en_region","region_id":"zona_equipo_cafe",
           "kind":"transicion","time":{"mode":"transition",
           "last_state_video_s":2350,"first_new_state_video_s":2352}}
        b={**a,"time":{"mode":"transition","last_state_video_s":2351,
                       "first_new_state_video_s":2353}}
        self.assertEqual(m.event_distance(a,b),0)

    def test_missing_count_not_equal(self):
        k=("A",2350,m.REGION)
        a={k:{"visibilidad_region":"parcial","barista_visibilidad":"visible",
              "minimo_recipientes_con_contenido":""}}
        b={k:{"visibilidad_region":"parcial","barista_visibilidad":"visible",
              "minimo_recipientes_con_contenido":"2"}}
        r=m.compare_coverage(a,b)
        self.assertEqual(r["counts_both_available"],0)
        self.assertIsNone(r["count_exact_agreement"])

if __name__=="__main__":unittest.main()
