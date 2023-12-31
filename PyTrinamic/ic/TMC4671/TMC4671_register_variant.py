'''
Created on 15.02.2019

@author: ED
'''

class TMC4671_register_variant:

    " ===== TMC4671 register variants ===== "

    CHIPINFO_ADDR_SI_TYPE                                   = 0
    CHIPINFO_ADDR_SI_VERSION                                = 1
    CHIPINFO_ADDR_SI_DATA                                   = 2
    CHIPINFO_ADDR_SI_TIME                                   = 3
    CHIPINFO_ADDR_SI_VARIANT                                = 4
    CHIPINFO_ADDR_SI_BUILD                                  = 5

    ADC_RAW_ADDR_ADC_I1_RAW_ADC_I0_RAW                      = 0
    ADC_RAW_ADDR_ADC_AGPI_A_RAW_ADC_VM_RAW                  = 1
    ADC_RAW_ADDR_ADC_AENC_UX_RAW_ADC_AGPI_B_RAW             = 2
    ADC_RAW_ADDR_ADC_AENC_WY_RAW_ADC_AENC_VN_RAW            = 3

    CONFIG_ADDR_biquad_x_a_1                                = 1
    CONFIG_ADDR_biquad_x_a_2                                = 2
    CONFIG_ADDR_biquad_x_b_0                                = 4
    CONFIG_ADDR_biquad_x_b_1                                = 5
    CONFIG_ADDR_biquad_x_b_2                                = 6
    CONFIG_ADDR_biquad_x_enable                             = 7
    CONFIG_ADDR_biquad_v_a_1                                = 9
    CONFIG_ADDR_biquad_v_a_2                                = 10
    CONFIG_ADDR_biquad_v_b_0                                = 12
    CONFIG_ADDR_biquad_v_b_1                                = 13
    CONFIG_ADDR_biquad_v_b_2                                = 14
    CONFIG_ADDR_biquad_v_enable                             = 15
    CONFIG_ADDR_biquad_t_a_1                                = 17
    CONFIG_ADDR_biquad_t_a_2                                = 18
    CONFIG_ADDR_biquad_t_b_0                                = 20
    CONFIG_ADDR_biquad_t_b_1                                = 21
    CONFIG_ADDR_biquad_t_b_2                                = 22
    CONFIG_ADDR_biquad_t_enable                             = 23
    CONFIG_ADDR_biquad_f_a_1                                = 25
    CONFIG_ADDR_biquad_f_a_2                                = 26
    CONFIG_ADDR_biquad_f_b_0                                = 28
    CONFIG_ADDR_biquad_f_b_1                                = 29
    CONFIG_ADDR_biquad_f_b_2                                = 30
    CONFIG_ADDR_biquad_f_enable                             = 31
    CONFIG_ADDR_prbs_amplitude                              = 32
    CONFIG_ADDR_prbs_down_sampling_ratio                    = 33
    CONFIG_ADDR_feed_forward_velocity_gain                  = 40
    CONFIG_ADDR_feed_forward_velicity_filter_constant       = 41
    CONFIG_ADDR_feed_forward_torque_gain                    = 42
    CONFIG_ADDR_feed_forward_torgue_filter_constant         = 43
    CONFIG_ADDR_VELOCITY_METER_PPTM_MIN_POS_DEV             = 50
    CONFIG_ADDR_ref_switch_config                           = 51
    CONFIG_ADDR_Encoder_Init_hall_Enable                    = 52
    CONFIG_ADDR_SINGLE_PIN_IF_STATUS_CFG                    = 60
    CONFIG_ADDR_SINGLE_PIN_IF_SCALE_OFFSET                  = 61

    PID_ERROR_ADDR_PID_TORQUE_ERROR                         = 0
    PID_ERROR_ADDR_PID_FLUX_ERROR                           = 1
    PID_ERROR_ADDR_PID_VELOCITY_ERROR                       = 2
    PID_ERROR_ADDR_PID_POSITION_ERROR                       = 3
    PID_ERROR_ADDR_PID_TORQUE_ERROR_SUM                     = 4
    PID_ERROR_ADDR_PID_FLUX_ERROR_SUM                       = 5
    PID_ERROR_ADDR_PID_VELOCITY_ERROR_SUM                   = 6
    PID_ERROR_ADDR_PID_POSITION_ERROR_SUM                   = 7

    INTERIM_ADDR_PIDIN_TARGET_TORQUE                        = 0
    INTERIM_ADDR_PIDIN_TARGET_FLUX                          = 1
    INTERIM_ADDR_PIDIN_TARGET_VELOCITY                      = 2
    INTERIM_ADDR_PIDIN_TARGET_POSITION                      = 3
    INTERIM_ADDR_PIDOUT_TARGET_TORQUE                       = 4
    INTERIM_ADDR_PIDOUT_TARGET_FLUX                         = 5
    INTERIM_ADDR_PIDOUT_TARGET_VELOCITY                     = 6
    INTERIM_ADDR_PIDOUT_TARGET_POSITION                     = 7
    INTERIM_ADDR_FOC_IWY_IUX                                = 8
    INTERIM_ADDR_FOC_IV                                     = 9
    INTERIM_ADDR_FOC_IB_IA                                  = 10
    INTERIM_ADDR_FOC_IQ_ID                                  = 11
    INTERIM_ADDR_FOC_UQ_UD                                  = 12
    INTERIM_ADDR_FOC_UQ_UD_LIMITED                          = 13
    INTERIM_ADDR_FOC_UB_UA                                  = 14
    INTERIM_ADDR_FOC_UWY_UUX                                = 15
    INTERIM_ADDR_FOC_UV                                     = 16
    INTERIM_ADDR_PWM_WY_UX                                  = 17
    INTERIM_ADDR_PWM_UV                                     = 18
    INTERIM_ADDR_ADC_I1_I0                                  = 19
    INTERIM_ADDR_PID_TORQUE_TARGET_FLUX_TARGET_TORQUE_ACTUAL_FLUX_ACTUAL_DIV256 = 20
    INTERIM_ADDR_PID_TORQUE_TARGET_TORQUE_ACTUAL            = 21
    INTERIM_ADDR_PID_FLUX_TARGET_FLUX_ACTUAL                = 22
    INTERIM_ADDR_PID_VELOCITY_TARGET_VELOCITY_ACTUAL_DIV256 = 23
    INTERIM_ADDR_PID_VELOCITY_TARGET_VELOCITY_ACTUAL        = 24
    INTERIM_ADDR_PID_POSITION_TARGET_POSITION_ACTUAL_DIV256 = 25
    INTERIM_ADDR_PID_POSITION_TARGET_POSITION_ACTUAL        = 26
    INTERIM_ADDR_FF_VELOCITY                                = 27
    INTERIM_ADDR_FF_TORQUE                                  = 28
    INTERIM_ADDR_ACTUAL_VELOCITY_PPTM                       = 29
    INTERIM_ADDR_REF_SWITCH_STATUS                          = 30
    INTERIM_ADDR_HOME_POSITION                              = 31
    INTERIM_ADDR_LEFT_POSITION                              = 32
    INTERIM_ADDR_RIGHT_POSITION                             = 33
    INTERIM_ADDR_ENC_INIT_HALL_STATUS                       = 34
    INTERIM_ADDR_ENC_INIT_HALL_PHI_E_ABN_OFFSET             = 35
    INTERIM_ADDR_ENC_INIT_HALL_PHI_E_AENC_OFFSET            = 36
    INTERIM_ADDR_ENC_INIT_HALL_PHI_A_AENC_OFFSET            = 37
    INTERIM_ADDR_enc_init_mini_move_u_d_status              = 40
    INTERIM_ADDR_enc_init_mini_move_phi_e_phi_e_offset      = 41
    INTERIM_ADDR_SINGLE_PIN_IF_PWM_DUTY_CYCLE_TORQUE_TARGET = 42
    INTERIM_ADDR_SINGLE_PIN_IF_VELOCITY_TARGET              = 43
    INTERIM_ADDR_SINGLE_PIN_IF_POSITION_TARGET              = 44
    INTERIM_ADDR_DEBUG_VALUE_1_0                            = 192
    INTERIM_ADDR_DEBUG_VALUE_3_2                            = 193
    INTERIM_ADDR_DEBUG_VALUE_5_4                            = 194
    INTERIM_ADDR_DEBUG_VALUE_7_6                            = 195
    INTERIM_ADDR_DEBUG_VALUE_9_8                            = 196
    INTERIM_ADDR_DEBUG_VALUE_11_10                          = 197
    INTERIM_ADDR_DEBUG_VALUE_13_12                          = 198
    INTERIM_ADDR_DEBUG_VALUE_15_14                          = 199
    INTERIM_ADDR_DEBUG_VALUE_16                             = 200
    INTERIM_ADDR_DEBUG_VALUE_17                             = 201
    INTERIM_ADDR_DEBUG_VALUE_18                             = 202
    INTERIM_ADDR_DEBUG_VALUE_19                             = 203
    INTERIM_ADDR_CONFIG_REG_0                               = 208
    INTERIM_ADDR_CONFIG_REG_1                               = 209
    INTERIM_ADDR_CTRL_PARAM_10                              = 210
    INTERIM_ADDR_CTRL_PARAM_32                              = 211
    INTERIM_ADDR_STATUS_REG_0                               = 212
    INTERIM_ADDR_STATUS_REG_1                               = 213
    INTERIM_ADDR_STATUS_PARAM_10                            = 214
    INTERIM_ADDR_STATUS_PARAM_32                            = 215
