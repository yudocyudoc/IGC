#if defined(__cplusplus)
  extern "C" {
#endif
  int artifacts_ct02_exact_two_m00_mayer(DATA* data, modelica_real** res, short*);
  int artifacts_ct02_exact_two_m00_lagrange(DATA* data, modelica_real** res, short *, short *);
  int artifacts_ct02_exact_two_m00_getInputVarIndicesInOptimization(DATA* data, int* input_var_indices);
  int artifacts_ct02_exact_two_m00_pickUpBoundsForInputsInOptimization(DATA* data, modelica_real* min, modelica_real* max, modelica_real*nominal, modelica_boolean *useNominal, char ** name, modelica_real * start, modelica_real * startTimeOpt);
  int artifacts_ct02_exact_two_m00_setInputData(DATA *data, const modelica_boolean file);
  int artifacts_ct02_exact_two_m00_getTimeGrid(DATA *data, modelica_integer * nsi, modelica_real**t);
#if defined(__cplusplus)
}
#endif
