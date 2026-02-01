/*      Compiler: ECL 24.5.10                                         */
/*      Date: 2026/1/31 16:07 (yyyy/mm/dd)                            */
/*      Machine: Darwin 23.6.0 arm64                                  */
/*      Source: /Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/pre-generated/src/algebra/MSET.lsp */
#include <ecl/ecl-cmp.h>
#include "/Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/_build/target/aarch64-apple-darwin23.6.0/algebra/MSET.eclh"
/*      function definition for MSET;elt                              */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L900_mset_elt_(cl_object v1_t_, cl_object v2_s_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4_a_;
  v4_a_ = ECL_NIL;
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[10];
   T0 = _ecl_car(v5);
   T1 = _ecl_cdr(v5);
   v4_a_ = (cl_env_copy->function=T0)->cfun.entry(3, v2_s_, v1_t_, T1);
  }
  T0 = ECL_CONS_CAR(v4_a_);
  if (!((ecl_fixnum(T0))==(1))) { goto L7; }
  value0 = ecl_make_fixnum(0);
  cl_env_copy->nvalues = 1;
  return value0;
L7:;
  value0 = ECL_CONS_CDR(v4_a_);
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;empty;%;2                        */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L901_mset_empty___2_(cl_object v1_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  v2 = (v1_)->vector.self.t[11];
  T1 = _ecl_car(v2);
  T2 = _ecl_cdr(v2);
  T0 = (cl_env_copy->function=T1)->cfun.entry(1, T2);
 }
 value0 = CONS(ecl_make_fixnum(0),T0);
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;multiset;%;3                     */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L902_mset_multiset___3_(cl_object v1_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  v2 = (v1_)->vector.self.t[12];
  T0 = _ecl_car(v2);
  T1 = _ecl_cdr(v2);
  value0 = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  return value0;
 }
}
/*      function definition for MSET;dictionary;%;4                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L903_mset_dictionary___4_(cl_object v1_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  v2 = (v1_)->vector.self.t[12];
  T0 = _ecl_car(v2);
  T1 = _ecl_cdr(v2);
  value0 = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  return value0;
 }
}
/*      function definition for MSET;set;%;5                          */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L904_mset_set___5_(cl_object v1_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  v2 = (v1_)->vector.self.t[12];
  T0 = _ecl_car(v2);
  T1 = _ecl_cdr(v2);
  value0 = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  return value0;
 }
}
/*      function definition for MSET;construct;L%;6                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L905_mset_construct_l__6_(cl_object v1_l_, cl_object v2_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3_n_;
  cl_object v4;
  cl_object v5_e_;
  cl_object v6_t_;
  v3_n_ = ecl_make_fixnum(0);
  v4 = ECL_NIL;
  v5_e_ = ECL_NIL;
  v6_t_ = ECL_NIL;
  {
   cl_object v7;
   v7 = (v2_)->vector.self.t[11];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   v6_t_ = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  }
  v3_n_ = ecl_make_fixnum(0);
  v5_e_ = ECL_NIL;
  v4 = v1_l_;
L12:;
  if (ECL_ATOM(v4)) { goto L20; }
  v5_e_ = _ecl_car(v4);
  goto L18;
L20:;
  goto L13;
L18:;
  {
   cl_object v7;
   v7 = (v2_)->vector.self.t[17];
   T0 = _ecl_car(v7);
   T1 = L900_mset_elt_(v6_t_, v5_e_, v2_);
   T2 = ecl_plus(T1,ecl_make_fixnum(1));
   T3 = _ecl_cdr(v7);
   (cl_env_copy->function=T0)->cfun.entry(4, v6_t_, v5_e_, T2, T3);
  }
  v3_n_ = ecl_plus(v3_n_,ecl_make_fixnum(1));
  goto L24;
L24:;
  v4 = _ecl_cdr(v4);
  goto L12;
L13:;
  goto L11;
L11:;
  value0 = CONS(v3_n_,v6_t_);
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;multiset;L%;7                    */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L906_mset_multiset_l__7_(cl_object v1_l_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[19];
  T0 = _ecl_car(v3);
  T1 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, v1_l_, T1);
  return value0;
 }
}
/*      function definition for MSET;dictionary;L%;8                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L907_mset_dictionary_l__8_(cl_object v1_l_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[19];
  T0 = _ecl_car(v3);
  T1 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, v1_l_, T1);
  return value0;
 }
}
/*      function definition for MSET;set;L%;9                         */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L908_mset_set_l__9_(cl_object v1_l_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[19];
  T0 = _ecl_car(v3);
  T1 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, v1_l_, T1);
  return value0;
 }
}
/*      function definition for MSET;multiset;S%;10                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L909_mset_multiset_s__10_(cl_object v1_s_, cl_object v2_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[19];
  T0 = _ecl_car(v3);
  T1 = ecl_list1(v1_s_);
  T2 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, T1, T2);
  return value0;
 }
}
/*      function definition for MSET;convert;%If;11                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L910_mset_convert__if_11_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1, T2, T3, T4, T5, T6;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[30];
  T0 = _ecl_car(v3);
  {
   cl_object v4;
   v4 = (v2_)->vector.self.t[26];
   T2 = _ecl_car(v4);
   T3 = _ecl_cdr(v4);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, VV[11], T3);
  }
  {
   cl_object v4;
   v4 = (v2_)->vector.self.t[28];
   T3 = _ecl_car(v4);
   {
    cl_object v5;
    v5 = (v2_)->vector.self.t[27];
    T5 = _ecl_car(v5);
    T6 = _ecl_cdr(v5);
    T4 = (cl_env_copy->function=T5)->cfun.entry(2, v1_ms_, T6);
   }
   T5 = _ecl_cdr(v4);
   T2 = (cl_env_copy->function=T3)->cfun.entry(2, T4, T5);
  }
  T3 = cl_list(2, T1, T2);
  T4 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, T3, T4);
  return value0;
 }
}
/*      function definition for MSET;members;%L;12                    */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L911_mset_members__l_12_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[32];
  T0 = _ecl_car(v3);
  T1 = ECL_CONS_CDR(v1_ms_);
  T2 = _ecl_cdr(v3);
  value0 = (cl_env_copy->function=T0)->cfun.entry(2, T1, T2);
  return value0;
 }
}
/*      function definition for MSET;coerce;%Of;13                    */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L912_mset_coerce__of_13_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3_l_;
  cl_object v4_item_;
  cl_object v5_n_;
  cl_object v6_ex_;
  cl_object v7;
  cl_object v8_e_;
  cl_object v9_colon_;
  cl_object v10_t_;
  v3_l_ = ECL_NIL;
  v4_item_ = ECL_NIL;
  v5_n_ = ecl_make_fixnum(0);
  v6_ex_ = ECL_NIL;
  v7 = ECL_NIL;
  v8_e_ = ECL_NIL;
  v9_colon_ = ECL_NIL;
  v10_t_ = ECL_NIL;
  v3_l_ = ECL_NIL;
  v10_t_ = ECL_CONS_CDR(v1_ms_);
  {
   cl_object v11;
   v11 = (v2_)->vector.self.t[36];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v9_colon_ = (cl_env_copy->function=T0)->cfun.entry(2, VV[14], T1);
  }
  v8_e_ = ECL_NIL;
  {
   cl_object v11;
   v11 = (v2_)->vector.self.t[32];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v7 = (cl_env_copy->function=T0)->cfun.entry(2, v10_t_, T1);
  }
L18:;
  if (ECL_ATOM(v7)) { goto L28; }
  v8_e_ = _ecl_car(v7);
  goto L26;
L28:;
  goto L19;
L26:;
  {
   cl_object v11;
   v11 = (v2_)->vector.self.t[37];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v6_ex_ = (cl_env_copy->function=T0)->cfun.entry(2, v8_e_, T1);
  }
  v5_n_ = L900_mset_elt_(v10_t_, v8_e_, v2_);
  if (!(ecl_greater(v5_n_,ecl_make_fixnum(1)))) { goto L41; }
  {
   cl_object v11;
   v11 = (v2_)->vector.self.t[39];
   T0 = _ecl_car(v11);
   {
    cl_object v12;
    v12 = (v2_)->vector.self.t[38];
    T2 = _ecl_car(v12);
    T3 = _ecl_cdr(v12);
    T1 = (cl_env_copy->function=T2)->cfun.entry(2, v5_n_, T3);
   }
   T2 = cl_list(3, T1, v9_colon_, v6_ex_);
   T3 = _ecl_cdr(v11);
   v4_item_ = (cl_env_copy->function=T0)->cfun.entry(2, T2, T3);
   goto L40;
  }
L41:;
  v4_item_ = v6_ex_;
L40:;
  v3_l_ = CONS(v4_item_,v3_l_);
  goto L32;
L32:;
  v7 = _ecl_cdr(v7);
  goto L18;
L19:;
  goto L17;
L17:;
  {
   cl_object v11;
   v11 = (v2_)->vector.self.t[40];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   value0 = (cl_env_copy->function=T0)->cfun.entry(2, v3_l_, T1);
   return value0;
  }
 }
}
/*      function definition for MSET;duplicates;%L;14                 */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L913_mset_duplicates__l_14_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3_ld_;
  cl_object v4;
  cl_object v5_n_;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8_t_;
  v3_ld_ = ECL_NIL;
  v4 = ECL_NIL;
  v5_n_ = ecl_make_fixnum(0);
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8_t_ = ECL_NIL;
  v3_ld_ = ECL_NIL;
  v8_t_ = ECL_CONS_CDR(v1_ms_);
  v7_e_ = ECL_NIL;
  {
   cl_object v9;
   v9 = (v2_)->vector.self.t[32];
   T0 = _ecl_car(v9);
   T1 = _ecl_cdr(v9);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v8_t_, T1);
  }
L12:;
  if (ECL_ATOM(v6)) { goto L22; }
  v7_e_ = _ecl_car(v6);
  goto L20;
L22:;
  goto L13;
L20:;
  v5_n_ = L900_mset_elt_(v8_t_, v7_e_, v2_);
  if (!(ecl_greater(v5_n_,ecl_make_fixnum(1)))) { goto L26; }
  {
   cl_object v9;
   v4 = v5_n_;
   v9 = v4;
   {
    bool v10;
    v10 = ecl_greatereq(v4,ecl_make_fixnum(0));
    if (!(ecl_make_bool(v10)==ECL_NIL)) { goto L34; }
   }
   T1 = ecl_function_dispatch(cl_env_copy,VV[76])(3, v4, VV[16], VV[17]) /*  coerce_failure_msg */;
   ecl_function_dispatch(cl_env_copy,VV[77])(1, T1) /*  error         */;
L34:;
   T0 = v9;
  }
  T1 = CONS(v7_e_,T0);
  v3_ld_ = CONS(T1,v3_ld_);
  goto L26;
L26:;
  v6 = _ecl_cdr(v6);
  goto L12;
L13:;
  goto L11;
L11:;
  value0 = v3_ld_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;extract!;%S;15                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L914_mset_extract___s_15_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3_n_;
  cl_object v4_e_;
  cl_object v5_t_;
  v3_n_ = ecl_make_fixnum(0);
  v4_e_ = ECL_NIL;
  v5_t_ = ECL_NIL;
  {
   cl_object v6;
   v6 = (v2_)->vector.self.t[46];
   T0 = _ecl_car(v6);
   T1 = _ecl_cdr(v6);
   if (Null((cl_env_copy->function=T0)->cfun.entry(2, v1_ms_, T1))) { goto L5; }
  }
  value0 = ecl_function_dispatch(cl_env_copy,VV[77])(1, VV[19]) /*  error */;
  return value0;
L5:;
  T0 = ECL_CONS_CAR(v1_ms_);
  T1 = ecl_minus(T0,ecl_make_fixnum(1));
  (ECL_CONS_CAR(v1_ms_)=T1,v1_ms_);
  v5_t_ = ECL_CONS_CDR(v1_ms_);
  {
   cl_object v6;
   v6 = (v2_)->vector.self.t[48];
   T1 = _ecl_car(v6);
   T2 = _ecl_cdr(v6);
   T0 = (cl_env_copy->function=T1)->cfun.entry(2, v5_t_, T2);
  }
  v4_e_ = ECL_CONS_CAR(T0);
  v3_n_ = L900_mset_elt_(v5_t_, v4_e_, v2_);
  if (!(ecl_greater(v3_n_,ecl_make_fixnum(1)))) { goto L22; }
  {
   cl_object v6;
   v6 = (v2_)->vector.self.t[17];
   T0 = _ecl_car(v6);
   T1 = ecl_minus(v3_n_,ecl_make_fixnum(1));
   T2 = _ecl_cdr(v6);
   (cl_env_copy->function=T0)->cfun.entry(4, v5_t_, v4_e_, T1, T2);
   goto L18;
  }
L22:;
  {
   cl_object v7;
   v7 = (v2_)->vector.self.t[49];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   (cl_env_copy->function=T0)->cfun.entry(3, v4_e_, v5_t_, T1);
   goto L18;
  }
L18:;
  value0 = v4_e_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;inspect;%S;16                    */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L915_mset_inspect__s_16_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = (v2_)->vector.self.t[48];
  T1 = _ecl_car(v3);
  T2 = ECL_CONS_CDR(v1_ms_);
  T3 = _ecl_cdr(v3);
  T0 = (cl_env_copy->function=T1)->cfun.entry(2, T2, T3);
 }
 value0 = ECL_CONS_CAR(T0);
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;insert!;S2%;17                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L916_mset_insert__s2__17_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3, T4, T5;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 T0 = ECL_CONS_CAR(v2_ms_);
 T1 = ecl_plus(T0,ecl_make_fixnum(1));
 (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[17];
  T0 = _ecl_car(v4);
  T1 = ECL_CONS_CDR(v2_ms_);
  T2 = ECL_CONS_CDR(v2_ms_);
  T3 = L900_mset_elt_(T2, v1_e_, v3_);
  T4 = ecl_plus(T3,ecl_make_fixnum(1));
  T5 = _ecl_cdr(v4);
  (cl_env_copy->function=T0)->cfun.entry(4, T1, v1_e_, T4, T5);
 }
 value0 = v2_ms_;
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;member?;S%B;18                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L917_mset_member__s_b_18_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3, T4;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[53];
  T0 = _ecl_car(v4);
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[32];
   T2 = _ecl_car(v5);
   T3 = ECL_CONS_CDR(v2_ms_);
   T4 = _ecl_cdr(v5);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, T3, T4);
  }
  T2 = _ecl_cdr(v4);
  value0 = (cl_env_copy->function=T0)->cfun.entry(3, v1_e_, T1, T2);
  return value0;
 }
}
/*      function definition for MSET;empty?;%B;19                     */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L918_mset_empty___b_19_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 T0 = ECL_CONS_CAR(v1_ms_);
 value0 = ecl_make_bool((T0)==(ecl_make_fixnum(0)));
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;#;%Nni;20                        */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L919_mset____nni_20_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  v3 = ECL_NIL;
  {
   cl_object v4;
   v3 = ECL_CONS_CAR(v1_ms_);
   v4 = v3;
   {
    bool v5;
    v5 = ecl_greatereq(v3,ecl_make_fixnum(0));
    if (!(ecl_make_bool(v5)==ECL_NIL)) { goto L4; }
   }
   T0 = ecl_function_dispatch(cl_env_copy,VV[76])(3, v3, VV[16], VV[17]) /*  coerce_failure_msg */;
   ecl_function_dispatch(cl_env_copy,VV[77])(1, T0) /*  error         */;
L4:;
   value0 = v4;
   cl_env_copy->nvalues = 1;
   return value0;
  }
 }
}
/*      function definition for MSET;count;S%Nni;21                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L920_mset_count_s_nni_21_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = ECL_NIL;
  {
   cl_object v5;
   T0 = ECL_CONS_CDR(v2_ms_);
   v4 = L900_mset_elt_(T0, v1_e_, v3_);
   v5 = v4;
   {
    bool v6;
    v6 = ecl_greatereq(v4,ecl_make_fixnum(0));
    if (!(ecl_make_bool(v6)==ECL_NIL)) { goto L4; }
   }
   T0 = ecl_function_dispatch(cl_env_copy,VV[76])(3, v4, VV[16], VV[17]) /*  coerce_failure_msg */;
   ecl_function_dispatch(cl_env_copy,VV[77])(1, T0) /*  error         */;
L4:;
   value0 = v5;
   cl_env_copy->nvalues = 1;
   return value0;
  }
 }
}
/*      function definition for MSET;remove!;S%I%;22                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L921_mset_remove__s_i__22_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_max_, cl_object v4_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v5_n_;
  cl_object v6_t_;
  v5_n_ = ecl_make_fixnum(0);
  v6_t_ = ECL_NIL;
  if (!(ecl_zerop(v3_max_))) { goto L4; }
  {
   cl_object v7;
   v7 = (v4_)->vector.self.t[58];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   value0 = (cl_env_copy->function=T0)->cfun.entry(3, v1_e_, v2_ms_, T1);
   return value0;
  }
L4:;
  v6_t_ = ECL_CONS_CDR(v2_ms_);
  {
   cl_object v8;
   v8 = (v4_)->vector.self.t[53];
   T0 = _ecl_car(v8);
   {
    cl_object v9;
    v9 = (v4_)->vector.self.t[32];
    T2 = _ecl_car(v9);
    T3 = _ecl_cdr(v9);
    T1 = (cl_env_copy->function=T2)->cfun.entry(2, v6_t_, T3);
   }
   T2 = _ecl_cdr(v8);
   if (Null((cl_env_copy->function=T0)->cfun.entry(3, v1_e_, T1, T2))) { goto L10; }
  }
  v5_n_ = L900_mset_elt_(v6_t_, v1_e_, v4_);
  if (!(ecl_lowereq(v5_n_,v3_max_))) { goto L20; }
  {
   cl_object v8;
   v8 = (v4_)->vector.self.t[49];
   T0 = _ecl_car(v8);
   T1 = _ecl_cdr(v8);
   (cl_env_copy->function=T0)->cfun.entry(3, v1_e_, v6_t_, T1);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v5_n_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  goto L10;
L20:;
  if (!(ecl_greater(v3_max_,ecl_make_fixnum(0)))) { goto L27; }
  {
   cl_object v8;
   v8 = (v4_)->vector.self.t[17];
   T0 = _ecl_car(v8);
   T1 = ecl_minus(v5_n_,v3_max_);
   T2 = _ecl_cdr(v8);
   (cl_env_copy->function=T0)->cfun.entry(4, v6_t_, v1_e_, T1, T2);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v3_max_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  goto L10;
L27:;
  v5_n_ = ecl_plus(v5_n_,v3_max_);
  if (!(ecl_greater(v5_n_,ecl_make_fixnum(0)))) { goto L10; }
  {
   cl_object v8;
   v8 = (v4_)->vector.self.t[17];
   T0 = _ecl_car(v8);
   T1 = ecl_negate(v3_max_);
   T2 = _ecl_cdr(v8);
   (cl_env_copy->function=T0)->cfun.entry(4, v6_t_, v1_e_, T1, T2);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v5_n_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  goto L10;
L10:;
  value0 = v2_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;remove!;M%I%;23                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L922_mset_remove__m_i__23_(cl_object v1_p_, cl_object v2_ms_, cl_object v3_max_, cl_object v4_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v5;
  cl_object v6_n_;
  cl_object v7;
  cl_object v8_e_;
  cl_object v9_t_;
  v5 = ECL_NIL;
  v6_n_ = ecl_make_fixnum(0);
  v7 = ECL_NIL;
  v8_e_ = ECL_NIL;
  v9_t_ = ECL_NIL;
  if (!(ecl_zerop(v3_max_))) { goto L7; }
  {
   cl_object v10;
   v10 = (v4_)->vector.self.t[61];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   value0 = (cl_env_copy->function=T0)->cfun.entry(3, v1_p_, v2_ms_, T1);
   return value0;
  }
L7:;
  v9_t_ = ECL_CONS_CDR(v2_ms_);
  v8_e_ = ECL_NIL;
  {
   cl_object v11;
   v11 = (v4_)->vector.self.t[32];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v7 = (cl_env_copy->function=T0)->cfun.entry(2, v9_t_, T1);
  }
L14:;
  if (ECL_ATOM(v7)) { goto L24; }
  v8_e_ = _ecl_car(v7);
  goto L22;
L24:;
  goto L15;
L22:;
  T0 = _ecl_car(v1_p_);
  T1 = _ecl_cdr(v1_p_);
  if (Null((cl_env_copy->function=T0)->cfun.entry(2, v8_e_, T1))) { goto L28; }
  v6_n_ = L900_mset_elt_(v9_t_, v8_e_, v4_);
  if (!(ecl_lowereq(v6_n_,v3_max_))) { goto L35; }
  {
   cl_object v11;
   v11 = (v4_)->vector.self.t[49];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   (cl_env_copy->function=T0)->cfun.entry(3, v8_e_, v9_t_, T1);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v6_n_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  goto L28;
L35:;
  if (!(ecl_greater(v3_max_,ecl_make_fixnum(0)))) { goto L42; }
  {
   cl_object v11;
   v11 = (v4_)->vector.self.t[17];
   T0 = _ecl_car(v11);
   T1 = ecl_minus(v6_n_,v3_max_);
   T2 = _ecl_cdr(v11);
   (cl_env_copy->function=T0)->cfun.entry(4, v9_t_, v8_e_, T1, T2);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v3_max_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  goto L28;
L42:;
  v6_n_ = ecl_plus(v6_n_,v3_max_);
  if (!(ecl_greater(v6_n_,ecl_make_fixnum(0)))) { goto L28; }
  {
   cl_object v11;
   v11 = (v4_)->vector.self.t[17];
   T0 = _ecl_car(v11);
   T1 = ecl_negate(v3_max_);
   T2 = _ecl_cdr(v11);
   (cl_env_copy->function=T0)->cfun.entry(4, v9_t_, v8_e_, T1, T2);
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = ecl_minus(T0,v6_n_);
  (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
  v5 = ECL_CONS_CAR(v2_ms_);
  goto L56;
L56:;
  goto L49;
L49:;
  goto L28;
L28:;
  v7 = _ecl_cdr(v7);
  goto L14;
L15:;
  goto L13;
L13:;
  value0 = v2_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;remove;S%I%;24                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L923_mset_remove_s_i__24_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_max_, cl_object v4_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v5;
  v5 = (v4_)->vector.self.t[59];
  T0 = _ecl_car(v5);
  {
   cl_object v6;
   v6 = (v4_)->vector.self.t[63];
   T2 = _ecl_car(v6);
   T3 = _ecl_cdr(v6);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, v2_ms_, T3);
  }
  T2 = _ecl_cdr(v5);
  value0 = (cl_env_copy->function=T0)->cfun.entry(4, v1_e_, T1, v3_max_, T2);
  return value0;
 }
}
/*      function definition for MSET;remove;M%I%;25                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L924_mset_remove_m_i__25_(cl_object v1_p_, cl_object v2_ms_, cl_object v3_max_, cl_object v4_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v5;
  v5 = (v4_)->vector.self.t[62];
  T0 = _ecl_car(v5);
  {
   cl_object v6;
   v6 = (v4_)->vector.self.t[63];
   T2 = _ecl_car(v6);
   T3 = _ecl_cdr(v6);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, v2_ms_, T3);
  }
  T2 = _ecl_cdr(v5);
  value0 = (cl_env_copy->function=T0)->cfun.entry(4, v1_p_, T1, v3_max_, T2);
  return value0;
 }
}
/*      function definition for MSET;remove!;S2%;26                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L925_mset_remove__s2__26_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4_t_;
  v4_t_ = ECL_NIL;
  v4_t_ = ECL_CONS_CDR(v2_ms_);
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[53];
   T0 = _ecl_car(v5);
   {
    cl_object v6;
    v6 = (v3_)->vector.self.t[32];
    T2 = _ecl_car(v6);
    T3 = _ecl_cdr(v6);
    T1 = (cl_env_copy->function=T2)->cfun.entry(2, v4_t_, T3);
   }
   T2 = _ecl_cdr(v5);
   if (Null((cl_env_copy->function=T0)->cfun.entry(3, v1_e_, T1, T2))) { goto L4; }
  }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = L900_mset_elt_(v4_t_, v1_e_, v3_);
  T2 = ecl_minus(T0,T1);
  (ECL_CONS_CAR(v2_ms_)=T2,v2_ms_);
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[49];
   T0 = _ecl_car(v5);
   T1 = _ecl_cdr(v5);
   (cl_env_copy->function=T0)->cfun.entry(3, v1_e_, v4_t_, T1);
   goto L4;
  }
L4:;
  value0 = v2_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;remove!;M2%;27                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L926_mset_remove__m2__27_(cl_object v1_p_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5_e_;
  cl_object v6_t_;
  v4 = ECL_NIL;
  v5_e_ = ECL_NIL;
  v6_t_ = ECL_NIL;
  v6_t_ = ECL_CONS_CDR(v2_ms_);
  v5_e_ = ECL_NIL;
  {
   cl_object v7;
   v7 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   v4 = (cl_env_copy->function=T0)->cfun.entry(2, v6_t_, T1);
  }
L7:;
  if (ECL_ATOM(v4)) { goto L17; }
  v5_e_ = _ecl_car(v4);
  goto L15;
L17:;
  goto L8;
L15:;
  T0 = _ecl_car(v1_p_);
  T1 = _ecl_cdr(v1_p_);
  if (Null((cl_env_copy->function=T0)->cfun.entry(2, v5_e_, T1))) { goto L21; }
  T0 = ECL_CONS_CAR(v2_ms_);
  T1 = L900_mset_elt_(v6_t_, v5_e_, v3_);
  T2 = ecl_minus(T0,T1);
  (ECL_CONS_CAR(v2_ms_)=T2,v2_ms_);
  {
   cl_object v7;
   v7 = (v3_)->vector.self.t[49];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   (cl_env_copy->function=T0)->cfun.entry(3, v5_e_, v6_t_, T1);
   goto L21;
  }
L21:;
  v4 = _ecl_cdr(v4);
  goto L7;
L8:;
  goto L6;
L6:;
  value0 = v2_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;select!;M2%;28                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L927_mset_select__m2__28_(cl_object v1_p_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[61];
  T0 = _ecl_car(v4);
  T1 = (VV[33]->symbol.gfdef);
  T2 = CONS(T1,v1_p_);
  T3 = _ecl_cdr(v4);
  value0 = (cl_env_copy->function=T0)->cfun.entry(3, T2, v2_ms_, T3);
  return value0;
 }
}
/*      function definition for MSET;select!;M2%;28!0                 */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L928_mset_select__m2__28_0_(cl_object v1_s1_, cl_object v2_p_)
{
 cl_object T0, T1, T2;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 T1 = _ecl_car(v2_p_);
 T2 = _ecl_cdr(v2_p_);
 T0 = (cl_env_copy->function=T1)->cfun.entry(2, v1_s1_, T2);
 value0 = ecl_make_bool(T0==ECL_NIL);
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;removeDuplicates!;2%;29          */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L929_mset_removeduplicates__2__29_(cl_object v1_ms_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3;
  cl_object v4_e_;
  cl_object v5_l_;
  cl_object v6_t_;
  v3 = ECL_NIL;
  v4_e_ = ECL_NIL;
  v5_l_ = ECL_NIL;
  v6_t_ = ECL_NIL;
  v6_t_ = ECL_CONS_CDR(v1_ms_);
  {
   cl_object v7;
   v7 = (v2_)->vector.self.t[32];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   v5_l_ = (cl_env_copy->function=T0)->cfun.entry(2, v6_t_, T1);
  }
  v4_e_ = ECL_NIL;
  v3 = v5_l_;
L12:;
  if (ECL_ATOM(v3)) { goto L20; }
  v4_e_ = _ecl_car(v3);
  goto L18;
L20:;
  goto L13;
L18:;
  {
   cl_object v7;
   v7 = (v2_)->vector.self.t[17];
   T0 = _ecl_car(v7);
   T1 = _ecl_cdr(v7);
   (cl_env_copy->function=T0)->cfun.entry(4, v6_t_, v4_e_, ecl_make_fixnum(1), T1);
   goto L24;
  }
L24:;
  v3 = _ecl_cdr(v3);
  goto L12;
L13:;
  goto L11;
L11:;
  {
   cl_fixnum v7;
   v7 = ecl_length(v5_l_);
   (ECL_CONS_CAR(v1_ms_)=ecl_make_fixnum(v7),v1_ms_);
  }
  value0 = v1_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;insert!;S%Nni%;30                */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L930_mset_insert__s_nni__30_(cl_object v1_e_, cl_object v2_ms_, cl_object v3_more_, cl_object v4_)
{
 cl_object T0, T1, T2, T3, T4, T5;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 T0 = ECL_CONS_CAR(v2_ms_);
 T1 = ecl_plus(T0,v3_more_);
 (ECL_CONS_CAR(v2_ms_)=T1,v2_ms_);
 {
  cl_object v5;
  v5 = (v4_)->vector.self.t[17];
  T0 = _ecl_car(v5);
  T1 = ECL_CONS_CDR(v2_ms_);
  T2 = ECL_CONS_CDR(v2_ms_);
  T3 = L900_mset_elt_(T2, v1_e_, v4_);
  T4 = ecl_plus(T3,v3_more_);
  T5 = _ecl_cdr(v5);
  (cl_env_copy->function=T0)->cfun.entry(4, T1, v1_e_, T4, T5);
 }
 value0 = v2_ms_;
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for MSET;map!;M2%;31                      */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L931_mset_map__m2__31_(cl_object v1_f_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5_e_;
  cl_object v6_t1_;
  cl_object v7_t_;
  v4 = ECL_NIL;
  v5_e_ = ECL_NIL;
  v6_t1_ = ECL_NIL;
  v7_t_ = ECL_NIL;
  v7_t_ = ECL_CONS_CDR(v2_ms_);
  {
   cl_object v8;
   v8 = (v3_)->vector.self.t[11];
   T0 = _ecl_car(v8);
   T1 = _ecl_cdr(v8);
   v6_t1_ = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  }
  v5_e_ = ECL_NIL;
  {
   cl_object v8;
   v8 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v8);
   T1 = _ecl_cdr(v8);
   v4 = (cl_env_copy->function=T0)->cfun.entry(2, v7_t_, T1);
  }
L12:;
  if (ECL_ATOM(v4)) { goto L22; }
  v5_e_ = _ecl_car(v4);
  goto L20;
L22:;
  goto L13;
L20:;
  {
   cl_object v8;
   v8 = (v3_)->vector.self.t[17];
   T0 = _ecl_car(v8);
   T2 = _ecl_car(v1_f_);
   T3 = _ecl_cdr(v1_f_);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, v5_e_, T3);
   T2 = L900_mset_elt_(v7_t_, v5_e_, v3_);
   T3 = _ecl_cdr(v8);
   (cl_env_copy->function=T0)->cfun.entry(4, v6_t1_, T1, T2, T3);
  }
  {
   cl_object v8;
   v8 = (v3_)->vector.self.t[49];
   T0 = _ecl_car(v8);
   T1 = _ecl_cdr(v8);
   (cl_env_copy->function=T0)->cfun.entry(3, v5_e_, v7_t_, T1);
   goto L26;
  }
L26:;
  v4 = _ecl_cdr(v4);
  goto L12;
L13:;
  goto L11;
L11:;
  (ECL_CONS_CDR(v2_ms_)=v6_t1_,v2_ms_);
  value0 = v2_ms_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;map;M2%;32                       */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L932_mset_map_m2__32_(cl_object v1_f_, cl_object v2_ms_, cl_object v3_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[70];
  T0 = _ecl_car(v4);
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[63];
   T2 = _ecl_car(v5);
   T3 = _ecl_cdr(v5);
   T1 = (cl_env_copy->function=T2)->cfun.entry(2, v2_ms_, T3);
  }
  T2 = _ecl_cdr(v4);
  value0 = (cl_env_copy->function=T0)->cfun.entry(3, v1_f_, T1, T2);
  return value0;
 }
}
/*      function definition for MSET;parts;%L;33                      */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L933_mset_parts__l_33_(cl_object v1_m_, cl_object v2_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v3_l_;
  cl_object v4;
  cl_object v5_i_;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8_t_;
  v3_l_ = ECL_NIL;
  v4 = ECL_NIL;
  v5_i_ = ECL_NIL;
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8_t_ = ECL_NIL;
  v3_l_ = ECL_NIL;
  v8_t_ = ECL_CONS_CDR(v1_m_);
  v7_e_ = ECL_NIL;
  {
   cl_object v9;
   v9 = (v2_)->vector.self.t[32];
   T0 = _ecl_car(v9);
   T1 = _ecl_cdr(v9);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v8_t_, T1);
  }
L12:;
  if (ECL_ATOM(v6)) { goto L22; }
  v7_e_ = _ecl_car(v6);
  goto L20;
L22:;
  goto L13;
L20:;
  v5_i_ = ecl_make_fixnum(1);
  v4 = L900_mset_elt_(v8_t_, v7_e_, v2_);
L28:;
  if (!((ecl_fixnum(v5_i_))>(ecl_fixnum(v4)))) { goto L34; }
  goto L29;
L34:;
  v3_l_ = CONS(v7_e_,v3_l_);
  goto L36;
L36:;
  v5_i_ = ecl_make_fixnum((ecl_fixnum(v5_i_))+1);
  goto L28;
L29:;
  goto L26;
L26:;
  v6 = _ecl_cdr(v6);
  goto L12;
L13:;
  goto L11;
L11:;
  value0 = v3_l_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;union;3%;34                      */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L934_mset_union_3__34_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1, T2, T3, T4;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5_e_;
  cl_object v6;
  cl_object v7_t2_;
  cl_object v8_t1_;
  cl_object v9_t_;
  v4 = ECL_NIL;
  v5_e_ = ECL_NIL;
  v6 = ECL_NIL;
  v7_t2_ = ECL_NIL;
  v8_t1_ = ECL_NIL;
  v9_t_ = ECL_NIL;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[11];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   v9_t_ = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  }
  v8_t1_ = ECL_CONS_CDR(v1_m1_);
  v7_t2_ = ECL_CONS_CDR(v2_m2_);
  v5_e_ = ECL_NIL;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v8_t1_, T1);
  }
L16:;
  if (ECL_ATOM(v6)) { goto L26; }
  v5_e_ = _ecl_car(v6);
  goto L24;
L26:;
  goto L17;
L24:;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[17];
   T0 = _ecl_car(v10);
   T1 = L900_mset_elt_(v8_t1_, v5_e_, v3_);
   T2 = _ecl_cdr(v10);
   (cl_env_copy->function=T0)->cfun.entry(4, v9_t_, v5_e_, T1, T2);
   goto L30;
  }
L30:;
  v6 = _ecl_cdr(v6);
  goto L16;
L17:;
  goto L15;
L15:;
  v5_e_ = ECL_NIL;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   v4 = (cl_env_copy->function=T0)->cfun.entry(2, v7_t2_, T1);
  }
L39:;
  if (ECL_ATOM(v4)) { goto L49; }
  v5_e_ = _ecl_car(v4);
  goto L47;
L49:;
  goto L40;
L47:;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[17];
   T0 = _ecl_car(v10);
   T1 = L900_mset_elt_(v7_t2_, v5_e_, v3_);
   T2 = L900_mset_elt_(v9_t_, v5_e_, v3_);
   T3 = ecl_plus(T1,T2);
   T4 = _ecl_cdr(v10);
   (cl_env_copy->function=T0)->cfun.entry(4, v9_t_, v5_e_, T3, T4);
   goto L53;
  }
L53:;
  v4 = _ecl_cdr(v4);
  goto L39;
L40:;
  goto L38;
L38:;
  T0 = ECL_CONS_CAR(v1_m1_);
  T1 = ECL_CONS_CAR(v2_m2_);
  T2 = ecl_plus(T0,T1);
  value0 = CONS(T2,v9_t_);
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;intersect;3%;35                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L935_mset_intersect_3__35_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4_n_;
  cl_object v5_m_;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8_t2_;
  cl_object v9_t1_;
  cl_object v10_t_;
  v4_n_ = ecl_make_fixnum(0);
  v5_m_ = ecl_make_fixnum(0);
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8_t2_ = ECL_NIL;
  v9_t1_ = ECL_NIL;
  v10_t_ = ECL_NIL;
  {
   cl_object v11;
   v11 = (v3_)->vector.self.t[11];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v10_t_ = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  }
  v9_t1_ = ECL_CONS_CDR(v1_m1_);
  v8_t2_ = ECL_CONS_CDR(v2_m2_);
  v4_n_ = ecl_make_fixnum(0);
  v7_e_ = ECL_NIL;
  {
   cl_object v11;
   v11 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v9_t1_, T1);
  }
L19:;
  if (ECL_ATOM(v6)) { goto L29; }
  v7_e_ = _ecl_car(v6);
  goto L27;
L29:;
  goto L20;
L27:;
  T0 = L900_mset_elt_(v9_t1_, v7_e_, v3_);
  T1 = L900_mset_elt_(v8_t2_, v7_e_, v3_);
  v5_m_ = ((ecl_float_nan_p(T1) || ecl_lowereq(T0,T1))?T0:T1);
  if (!(ecl_greater(v5_m_,ecl_make_fixnum(0)))) { goto L33; }
  T0 = L900_mset_elt_(v9_t1_, v7_e_, v3_);
  T1 = L900_mset_elt_(v8_t2_, v7_e_, v3_);
  v5_m_ = ecl_plus(T0,T1);
  {
   cl_object v11;
   v11 = (v3_)->vector.self.t[17];
   T0 = _ecl_car(v11);
   T1 = _ecl_cdr(v11);
   (cl_env_copy->function=T0)->cfun.entry(4, v10_t_, v7_e_, v5_m_, T1);
  }
  v4_n_ = ecl_plus(v4_n_,v5_m_);
  goto L33;
L33:;
  v6 = _ecl_cdr(v6);
  goto L19;
L20:;
  goto L18;
L18:;
  value0 = CONS(v4_n_,v10_t_);
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;difference;3%;36                 */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L936_mset_difference_3__36_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4_n_;
  cl_object v5_k2_;
  cl_object v6_k1_;
  cl_object v7;
  cl_object v8_e_;
  cl_object v9_t2_;
  cl_object v10_t1_;
  cl_object v11_t_;
  v4_n_ = ecl_make_fixnum(0);
  v5_k2_ = ecl_make_fixnum(0);
  v6_k1_ = ecl_make_fixnum(0);
  v7 = ECL_NIL;
  v8_e_ = ECL_NIL;
  v9_t2_ = ECL_NIL;
  v10_t1_ = ECL_NIL;
  v11_t_ = ECL_NIL;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[11];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   v11_t_ = (cl_env_copy->function=T0)->cfun.entry(1, T1);
  }
  v10_t1_ = ECL_CONS_CDR(v1_m1_);
  v9_t2_ = ECL_CONS_CDR(v2_m2_);
  v4_n_ = ecl_make_fixnum(0);
  v8_e_ = ECL_NIL;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   v7 = (cl_env_copy->function=T0)->cfun.entry(2, v10_t1_, T1);
  }
L20:;
  if (ECL_ATOM(v7)) { goto L30; }
  v8_e_ = _ecl_car(v7);
  goto L28;
L30:;
  goto L21;
L28:;
  v6_k1_ = L900_mset_elt_(v10_t1_, v8_e_, v3_);
  v5_k2_ = L900_mset_elt_(v9_t2_, v8_e_, v3_);
  if (!(ecl_greater(v6_k1_,ecl_make_fixnum(0)))) { goto L34; }
  if (!((v5_k2_)==(ecl_make_fixnum(0)))) { goto L34; }
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[17];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   (cl_env_copy->function=T0)->cfun.entry(4, v11_t_, v8_e_, v6_k1_, T1);
  }
  v4_n_ = ecl_plus(v4_n_,v6_k1_);
  goto L34;
L34:;
  v7 = _ecl_cdr(v7);
  goto L20;
L21:;
  goto L19;
L19:;
  if (!((v4_n_)==(ecl_make_fixnum(0)))) { goto L52; }
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[12];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   value0 = (cl_env_copy->function=T0)->cfun.entry(1, T1);
   return value0;
  }
L52:;
  value0 = CONS(v4_n_,v11_t_);
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;symmetricDifference;3%;37        */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L937_mset_symmetricdifference_3__37_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1, T2, T3, T4;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[72];
  T0 = _ecl_car(v4);
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[74];
   T2 = _ecl_car(v5);
   T3 = _ecl_cdr(v5);
   T1 = (cl_env_copy->function=T2)->cfun.entry(3, v1_m1_, v2_m2_, T3);
  }
  {
   cl_object v5;
   v5 = (v3_)->vector.self.t[74];
   T3 = _ecl_car(v5);
   T4 = _ecl_cdr(v5);
   T2 = (cl_env_copy->function=T3)->cfun.entry(3, v2_m2_, v1_m1_, T4);
  }
  T3 = _ecl_cdr(v4);
  value0 = (cl_env_copy->function=T0)->cfun.entry(3, T1, T2, T3);
  return value0;
 }
}
/*      function definition for MSET;=;2%B;38                         */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L938_mset___2_b_38_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1, T2, T3;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8;
  cl_object v9;
  cl_object v10_t2_;
  cl_object v11_t1_;
  v4 = ECL_NIL;
  v5 = ECL_NIL;
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8 = ECL_NIL;
  v9 = ECL_NIL;
  v10_t2_ = ECL_NIL;
  v11_t1_ = ECL_NIL;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[76];
   T0 = _ecl_car(v12);
   T1 = ECL_CONS_CAR(v1_m1_);
   T2 = ECL_CONS_CAR(v2_m2_);
   T3 = _ecl_cdr(v12);
   if (Null((cl_env_copy->function=T0)->cfun.entry(3, T1, T2, T3))) { goto L11; }
  }
  value0 = ECL_NIL;
  cl_env_copy->nvalues = 1;
  return value0;
L11:;
  v11_t1_ = ECL_CONS_CDR(v1_m1_);
  v10_t2_ = ECL_CONS_CDR(v2_m2_);
  v7_e_ = ECL_NIL;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   v9 = (cl_env_copy->function=T0)->cfun.entry(2, v11_t1_, T1);
  }
L22:;
  if (ECL_ATOM(v9)) { goto L32; }
  v7_e_ = _ecl_car(v9);
  goto L30;
L32:;
  goto L23;
L30:;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[76];
   T0 = _ecl_car(v12);
   T1 = L900_mset_elt_(v11_t1_, v7_e_, v3_);
   T2 = L900_mset_elt_(v10_t2_, v7_e_, v3_);
   T3 = _ecl_cdr(v12);
   if (Null((cl_env_copy->function=T0)->cfun.entry(3, T1, T2, T3))) { goto L36; }
  }
  v5 = ECL_NIL;
  goto L9;
  goto L20;
L36:;
  v9 = _ecl_cdr(v9);
  goto L22;
L23:;
  goto L19;
L20:;
  goto L19;
L19:;
  v7_e_ = ECL_NIL;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v12);
   T1 = _ecl_cdr(v12);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v10_t2_, T1);
  }
L53:;
  if (ECL_ATOM(v6)) { goto L63; }
  v7_e_ = _ecl_car(v6);
  goto L61;
L63:;
  goto L54;
L61:;
  {
   cl_object v12;
   v12 = (v3_)->vector.self.t[76];
   T0 = _ecl_car(v12);
   T1 = L900_mset_elt_(v11_t1_, v7_e_, v3_);
   T2 = L900_mset_elt_(v10_t2_, v7_e_, v3_);
   T3 = _ecl_cdr(v12);
   if (Null((cl_env_copy->function=T0)->cfun.entry(3, T1, T2, T3))) { goto L67; }
  }
  v5 = ECL_NIL;
  goto L9;
  goto L51;
L67:;
  v6 = _ecl_cdr(v6);
  goto L53;
L54:;
  goto L50;
L51:;
  goto L50;
L50:;
  value0 = ECL_T;
  cl_env_copy->nvalues = 1;
  return value0;
L9:;
  value0 = v5;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;<;2%B;39                         */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L939_mset___2_b_39_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8_t2_;
  cl_object v9_t1_;
  v4 = ECL_NIL;
  v5 = ECL_NIL;
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8_t2_ = ECL_NIL;
  v9_t1_ = ECL_NIL;
  T0 = ECL_CONS_CAR(v1_m1_);
  T1 = ECL_CONS_CAR(v2_m2_);
  if (!(ecl_greatereq(T0,T1))) { goto L9; }
  value0 = ECL_NIL;
  cl_env_copy->nvalues = 1;
  return value0;
L9:;
  v9_t1_ = ECL_CONS_CDR(v1_m1_);
  v8_t2_ = ECL_CONS_CDR(v2_m2_);
  v7_e_ = ECL_NIL;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v9_t1_, T1);
  }
L18:;
  if (ECL_ATOM(v6)) { goto L28; }
  v7_e_ = _ecl_car(v6);
  goto L26;
L28:;
  goto L19;
L26:;
  T0 = L900_mset_elt_(v9_t1_, v7_e_, v3_);
  T1 = L900_mset_elt_(v8_t2_, v7_e_, v3_);
  if (!(ecl_greater(T0,T1))) { goto L32; }
  v5 = ECL_NIL;
  goto L7;
  goto L16;
L32:;
  v6 = _ecl_cdr(v6);
  goto L18;
L19:;
  goto L15;
L16:;
  goto L15;
L15:;
  T0 = ECL_CONS_CAR(v1_m1_);
  T1 = ECL_CONS_CAR(v2_m2_);
  value0 = ecl_make_bool(ecl_lower(T0,T1));
  cl_env_copy->nvalues = 1;
  return value0;
L7:;
  value0 = v5;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;subset?;2%B;40                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L940_mset_subset__2_b_40_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  cl_object v5;
  cl_object v6;
  cl_object v7_e_;
  cl_object v8_t2_;
  cl_object v9_t1_;
  v4 = ECL_NIL;
  v5 = ECL_NIL;
  v6 = ECL_NIL;
  v7_e_ = ECL_NIL;
  v8_t2_ = ECL_NIL;
  v9_t1_ = ECL_NIL;
  T0 = ECL_CONS_CAR(v1_m1_);
  T1 = ECL_CONS_CAR(v2_m2_);
  if (!(ecl_greater(T0,T1))) { goto L9; }
  value0 = ECL_NIL;
  cl_env_copy->nvalues = 1;
  return value0;
L9:;
  v9_t1_ = ECL_CONS_CDR(v1_m1_);
  v8_t2_ = ECL_CONS_CDR(v2_m2_);
  v7_e_ = ECL_NIL;
  {
   cl_object v10;
   v10 = (v3_)->vector.self.t[32];
   T0 = _ecl_car(v10);
   T1 = _ecl_cdr(v10);
   v6 = (cl_env_copy->function=T0)->cfun.entry(2, v9_t1_, T1);
  }
L18:;
  if (ECL_ATOM(v6)) { goto L28; }
  v7_e_ = _ecl_car(v6);
  goto L26;
L28:;
  goto L19;
L26:;
  T0 = L900_mset_elt_(v9_t1_, v7_e_, v3_);
  T1 = L900_mset_elt_(v8_t2_, v7_e_, v3_);
  if (!(ecl_greater(T0,T1))) { goto L32; }
  v5 = ECL_NIL;
  goto L7;
  goto L16;
L32:;
  v6 = _ecl_cdr(v6);
  goto L18;
L19:;
  goto L15;
L16:;
  goto L15;
L15:;
  value0 = ECL_T;
  cl_env_copy->nvalues = 1;
  return value0;
L7:;
  value0 = v5;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for MSET;<=;2%B;41                        */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L941_mset____2_b_41_(cl_object v1_m1_, cl_object v2_m2_, cl_object v3_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  v4 = (v3_)->vector.self.t[79];
  T0 = _ecl_car(v4);
  T1 = _ecl_cdr(v4);
  value0 = (cl_env_copy->function=T0)->cfun.entry(3, v1_m1_, v2_m2_, T1);
  return value0;
 }
}
/*      function definition for Multiset;                             */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L942_multiset__(cl_object v1__1_)
{
 cl_object T0, T1, T2, T3, T4, T5, T6;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  cl_object v3_pv__;
  cl_object v4_;
  cl_object v5_dv__;
  cl_object v6dv_1;
  v2 = ECL_NIL;
  v3_pv__ = ECL_NIL;
  v4_ = ECL_NIL;
  v5_dv__ = ECL_NIL;
  v6dv_1 = ECL_NIL;
  v6dv_1 = ecl_function_dispatch(cl_env_copy,VV[107])(1, v1__1_) /*  devaluate */;
  v5_dv__ = cl_list(2, VV[48], v6dv_1);
  v4_ = ecl_function_dispatch(cl_env_copy,VV[108])(1, ecl_make_fixnum(86)) /*  GETREFV */;
  (v4_)->vector.self.t[0]= v5_dv__;
  T1 = ecl_function_dispatch(cl_env_copy,VV[107])(1, v1__1_) /*  devaluate */;
  T2 = cl_list(2, VV[49], T1);
  if (Null(ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, T2) /*  HasCategory */)) { goto L17; }
  T0 = ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[50]) /*  HasCategory */;
  goto L15;
L17:;
  T0 = ECL_NIL;
  goto L15;
L15:;
  T1 = ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[51]) /*  HasCategory */;
  T2 = ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[52]) /*  HasCategory */;
  T3 = ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[53]) /*  HasCategory */;
  T4 = cl_list(4, T0, T1, T2, T3);
  v3_pv__ = ecl_function_dispatch(cl_env_copy,VV[110])(3, ecl_make_fixnum(0), ecl_make_fixnum(0), T4) /*  buildPredVector */;
  (v4_)->vector.self.t[3]= v3_pv__;
  T0 = ecl_list1(v6dv_1);
  T1 = CONS(ecl_make_fixnum(1),v4_);
  ecl_function_dispatch(cl_env_copy,VV[111])(4, ECL_SYM_VAL(cl_env_copy,VV[54]), VV[48], T0, T1) /*  haddProp */;
  ecl_function_dispatch(cl_env_copy,VV[112])(1, v4_) /*  stuffDomainSlots */;
  (v4_)->vector.self.t[6]= v1__1_;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[109])(2, v4_, VV[55]) /*  HasCategory */)) { goto L24; }
  ecl_function_dispatch(cl_env_copy,VV[113])(2, v4_, ecl_make_fixnum(16)) /*  augmentPredVector */;
  goto L22;
L24:;
  goto L22;
L22:;
  v2 = ecl_function_dispatch(cl_env_copy,VV[109])(2, v4_, VV[56]) /*  HasCategory */;
  if (Null(v2)) { goto L28; }
  ecl_function_dispatch(cl_env_copy,VV[113])(2, v4_, ecl_make_fixnum(32)) /*  augmentPredVector */;
  goto L26;
L28:;
  goto L26;
L26:;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[52]) /*  HasCategory */)) { goto L33; }
  if (Null(v2)) { goto L33; }
  ecl_function_dispatch(cl_env_copy,VV[113])(2, v4_, ecl_make_fixnum(64)) /*  augmentPredVector */;
  goto L31;
L33:;
  goto L31;
L31:;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[109])(2, v1__1_, VV[53]) /*  HasCategory */)) { goto L38; }
  if (Null(v2)) { goto L38; }
  ecl_function_dispatch(cl_env_copy,VV[113])(2, v4_, ecl_make_fixnum(128)) /*  augmentPredVector */;
  goto L36;
L38:;
  goto L36;
L36:;
  v3_pv__ = (v4_)->vector.self.t[3];
  T0 = ecl_function_dispatch(cl_env_copy,VV[114])(0) /*  Integer      */;
  T1 = CONS(VV[57],T0);
  T2 = ecl_function_dispatch(cl_env_copy,VV[114])(0) /*  Integer      */;
  T3 = ecl_function_dispatch(cl_env_copy,VV[115])(2, v1__1_, T2) /*  Table */;
  T4 = CONS(VV[58],T3);
  T5 = cl_list(2, T1, T4);
  T6 = ecl_function_dispatch(cl_env_copy,VV[116])(1, T5) /*  Record0  */;
  (v4_)->vector.self.t[7]= T6;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[117])(2, v3_pv__, ecl_make_fixnum(2)) /*  testBitVector */)) { goto L44; }
  T0 = (VV[10]->symbol.gfdef);
  T1 = CONS(T0,v4_);
  (v4_)->vector.self.t[31]= T1;
L44:;
  value0 = v4_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for Multiset                              */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L943_multiset_(cl_object volatile v1)
{
 cl_object T0, T1, T2;
 cl_object volatile env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object volatile value0;
TTL:
 {
  volatile cl_object v2;
  v2 = ECL_NIL;
  T0 = ecl_function_dispatch(cl_env_copy,VV[107])(1, v1) /*  devaluate */;
  T1 = ecl_list1(T0);
  T2 = ecl_gethash_safe(VV[48],ECL_SYM_VAL(cl_env_copy,VV[54]),ECL_NIL);
  v2 = ecl_function_dispatch(cl_env_copy,VV[119])(3, T1, T2, VV[59]) /*  lassocShiftWithFunction */;
  if (Null(v2)) { goto L3; }
  value0 = ecl_function_dispatch(cl_env_copy,VV[120])(1, v2) /*  CDRwithIncrement */;
  return value0;
L3:;
  {
   volatile bool unwinding = FALSE;
   cl_index v3=ECL_STACK_INDEX(cl_env_copy),v4;
   ecl_frame_ptr next_fr;
   ecl_frs_push(cl_env_copy,ECL_PROTECT_TAG);
   if (__ecl_frs_push_result) {
     unwinding = TRUE; next_fr=cl_env_copy->nlj_fr;
   } else {
   {
    cl_object v5;
    v5 = ecl_function_dispatch(cl_env_copy,VV[47])(1, v1) /*  Multiset; */;
    v2 = ECL_T;
    cl_env_copy->values[0] = v5;
    cl_env_copy->nvalues = 1;
   }
   }
   ecl_frs_pop(cl_env_copy);
   v4=ecl_stack_push_values(cl_env_copy);
   if ((v2)!=ECL_NIL) { goto L10; }
   cl_remhash(VV[48], ECL_SYM_VAL(cl_env_copy,VV[54]));
L10:;
   ecl_stack_pop_values(cl_env_copy,v4);
   if (unwinding) ecl_unwind(cl_env_copy,next_fr);
   ECL_STACK_SET_INDEX(cl_env_copy,v3);
   return cl_env_copy->values[0];
  }
 }
}