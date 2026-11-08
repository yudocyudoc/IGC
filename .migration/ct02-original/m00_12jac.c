/* Jacobians 6 */
#include "artifacts/ct02-exact-two/m00_model.h"
#include "artifacts/ct02-exact-two/m00_12jac.h"
#include "simulation/jacobian_util.h"
#include "util/omc_file.h"
int artifacts_ct02_exact_two_m00_functionJacH_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_m00_functionJacF_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_m00_functionJacD_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_m00_functionJacC_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_m00_functionJacB_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
/* constant equations */
/* dynamic equations */

OMC_DISABLE_OPT
int artifacts_ct02_exact_two_m00_functionJacA_constantEqns(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = artifacts_ct02_exact_two_m00_INDEX_JAC_A;
  
  
  return 0;
}

int artifacts_ct02_exact_two_m00_functionJacA_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = artifacts_ct02_exact_two_m00_INDEX_JAC_A;
  
  
  return 0;
}

int artifacts_ct02_exact_two_m00_initialAnalyticJacobianH(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_m00_initialAnalyticJacobianF(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_m00_initialAnalyticJacobianD(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_m00_initialAnalyticJacobianC(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_m00_initialAnalyticJacobianB(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
OMC_DISABLE_OPT
int artifacts_ct02_exact_two_m00_initialAnalyticJacobianA(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  size_t count;

  FILE* pFile = openSparsePatternFile(data, threadData, "artifacts/ct02-exact-two/m00_JacA.bin");
  
  initJacobian(jacobian, 4, 4, 0, artifacts_ct02_exact_two_m00_functionJacA_column, NULL, NULL);
  jacobian->sparsePattern = allocSparsePattern(4, 6, 2);
  jacobian->availability = JACOBIAN_ONLY_SPARSITY;
  
  /* read lead index of compressed sparse column */
  count = omc_fread(jacobian->sparsePattern->leadindex, sizeof(unsigned int), 4+1, pFile, FALSE);
  if (count != 4+1) {
    throwStreamPrint(threadData, "Error while reading lead index list of sparsity pattern. Expected %d, got %zu", 4+1, count);
  }
  
  /* read sparse index */
  count = omc_fread(jacobian->sparsePattern->index, sizeof(unsigned int), 6, pFile, FALSE);
  if (count != 6) {
    throwStreamPrint(threadData, "Error while reading row index list of sparsity pattern. Expected %d, got %zu", 6, count);
  }
  
  /* write color array */
  /* color 1 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 1, 1, 4);
  /* color 2 with 3 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 2, 3, 4);
  
  omc_fclose(pFile);
  
  return 0;
}


