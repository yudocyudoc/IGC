/* Jacobians 6 */
#include "artifacts/ct02-exact-two/d00_model.h"
#include "artifacts/ct02-exact-two/d00_12jac.h"
#include "simulation/jacobian_util.h"
#include "util/omc_file.h"
int artifacts_ct02_exact_two_d00_functionJacH_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_d00_functionJacF_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_d00_functionJacD_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_d00_functionJacC_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
int artifacts_ct02_exact_two_d00_functionJacB_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}
/* constant equations */
/* dynamic equations */

OMC_DISABLE_OPT
int artifacts_ct02_exact_two_d00_functionJacA_constantEqns(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = artifacts_ct02_exact_two_d00_INDEX_JAC_A;
  
  
  return 0;
}

int artifacts_ct02_exact_two_d00_functionJacA_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = artifacts_ct02_exact_two_d00_INDEX_JAC_A;
  
  
  return 0;
}

int artifacts_ct02_exact_two_d00_initialAnalyticJacobianH(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianF(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianD(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianC(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianB(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
OMC_DISABLE_OPT
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianA(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  size_t count;

  FILE* pFile = openSparsePatternFile(data, threadData, "artifacts/ct02-exact-two/d00_JacA.bin");
  
  initJacobian(jacobian, 3, 3, 0, artifacts_ct02_exact_two_d00_functionJacA_column, NULL, NULL);
  jacobian->sparsePattern = allocSparsePattern(3, 2, 1);
  jacobian->availability = JACOBIAN_ONLY_SPARSITY;
  
  /* read lead index of compressed sparse column */
  count = omc_fread(jacobian->sparsePattern->leadindex, sizeof(unsigned int), 3+1, pFile, FALSE);
  if (count != 3+1) {
    throwStreamPrint(threadData, "Error while reading lead index list of sparsity pattern. Expected %d, got %zu", 3+1, count);
  }
  
  /* read sparse index */
  count = omc_fread(jacobian->sparsePattern->index, sizeof(unsigned int), 2, pFile, FALSE);
  if (count != 2) {
    throwStreamPrint(threadData, "Error while reading row index list of sparsity pattern. Expected %d, got %zu", 2, count);
  }
  
  /* write color array */
  /* color 1 with 3 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 1, 3, 3);
  
  omc_fclose(pFile);
  
  return 0;
}


