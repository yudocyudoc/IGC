/* Jacobians */
static const REAL_ATTRIBUTE dummyREAL_ATTRIBUTE = omc_dummyRealAttribute;

#if defined(__cplusplus)
extern "C" {
#endif

/* Jacobian Variables */
#define artifacts_ct02_exact_two_d00_INDEX_JAC_H 0
int artifacts_ct02_exact_two_d00_functionJacH_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianH(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define artifacts_ct02_exact_two_d00_INDEX_JAC_F 1
int artifacts_ct02_exact_two_d00_functionJacF_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianF(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define artifacts_ct02_exact_two_d00_INDEX_JAC_D 2
int artifacts_ct02_exact_two_d00_functionJacD_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianD(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define artifacts_ct02_exact_two_d00_INDEX_JAC_C 3
int artifacts_ct02_exact_two_d00_functionJacC_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianC(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define artifacts_ct02_exact_two_d00_INDEX_JAC_B 4
int artifacts_ct02_exact_two_d00_functionJacB_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianB(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define artifacts_ct02_exact_two_d00_INDEX_JAC_A 5
int artifacts_ct02_exact_two_d00_functionJacA_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int artifacts_ct02_exact_two_d00_initialAnalyticJacobianA(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);

#if defined(__cplusplus)
}
#endif
