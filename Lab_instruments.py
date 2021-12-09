"""
Description: A python library that wraps up the GPIB commands for lab instruments
Python version: 3.9
Anaconda version: 4.11.0    https://www.anaconda.com/products/individual
NI visa version: 21.0       https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html#409839
Installed additional libraries: pyvisa, pyvisa-py, gpib-ctypes

Project webpage: https://github.com/FranklinLu111/Lab_instruments
Recommended python editor: pycharm
To see detailed information of methods when using them, position the caret at the function name and press Ctrl+Q
Use Ctrl+Shift+NumPad - / Ctrl+Shift+NumPad + to collapse or expand fragments

set: PC -> Instrument
get: PC <- Instrument
Example:
    a = KEI2600B('GPIB0::1::INSTR')
    a.set_limit(1, 1, 1e-3)
    a.set_voltage(1, 0.22)
    a.set_output_state(1, 'ON')
    measurement = a.get_current_voltage(1)
"""
import pyvisa
import ok
import time
from warnings import warn


class KEI2230G:  # 3-channel DC power supply from Keithley
    """
    Programmer Manual:
    https://download.tek.com/manual/2230G-900-01A_Jun_2018_User.pdf
    Useful information of coding starts from chapter 4
    """

    def __init__(self, instrument_id):
        """
        :param str instrument_id: GPIB address of target device
        """
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(instrument_id)
        self.safety = [0, 0, 0]
        print('Initialized  ' + self.device.query('*IDN?'))
        return

    def set_output_state(self, ONorOFF):
        """
        :param str ONorOFF: 'ON' or 'OFF'
        """
        self.device.write('OUTP ' + ONorOFF)
        return

    def set_voltage(self, channel, voltage, unit='mV'):
        """
        Set the output voltage of a specified channel
        :param int channel: selected channel: 1, 2, 3
        :param float voltage: output voltage
        :param str unit: 'mV'(default) or 'V'
        """
        if self.safety[channel - 1] == 0:
            warn("Maximum voltage is not set. Run set_voltage_limit first to protect your circuit",
                 stacklevel=2)
            return -1
        self.device.write('INSTrument:NSELect ' + str(channel))
        self.device.write('SOURce' + ':VOLTage:LEVel:IMMediate:AMPLitude ' + str(voltage) + unit)

    def set_current(self, channel, current, unit='mA'):
        """
        Set the output current of a specified channel
        :param int channel: selected channel: 1, 2, 3
        :param float voltage: output current
        :param str unit: 'mA'(default) or 'A'
        """
        if self.safety[channel - 1] == 0:
            warn("Maximum voltage is not set. Run set_voltage_limit first to protect your circuit",
                 stacklevel=2)
            return -1
        self.device.write('INSTrument:NSELect ' + str(channel))
        self.device.write('SOURce' + ':CURRent:LEVel:IMMediate:AMPLitude ' + str(current) + unit)

    def set_voltage_limit(self, channel, voltage_lim):
        """
        Set the limit of output voltage of a specified channel. Unit is 'V'
        :param int channel: selected channel: 1, 2, 3
        :param float voltage: output voltage limit/V
        """
        self.device.write('INSTrument:NSELect ' + str(channel))
        self.device.write('SOURce:VOLTage:LIMit:LEVel ' + str(voltage_lim))
        self.safety[channel - 1] = 1

    def get_voltage(self, channel):
        """
        :param channel: selected channel: 1, 2, 3
        :return: measured voltage on the specified channel
        """
        return float(self.device.query('measure:SCALar:voltage:DC? CH' + str(channel)))

    def get_current(self, channel):
        """
        :param channel: selected channel: 1, 2, 3
        :return: measured current on the specified channel
        """
        return float(self.device.query('measure:SCALar:current:DC? CH' + str(channel)))


class KEI2600B:  # 2600B series sourcemeter from Keithley
    """
    Channel A,B is mapped to Channel 1,2
    programmer manual: https://www.tek.com/keithley-source-measure-units/smu-2600b-series-sourcemeter-manual-8
    """

    def __init__(self, instrument_id):
        """
        :param str instrument_id: GPIB address of target device
        """
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(instrument_id)
        self.ch_map = {
            1: 'a',
            2: 'b'
        }
        self.safety = [0, 0]
        print('Initialized  ' + self.device.query('*IDN?'))
        return

    def set_output_state(self, channel, ONorOFF):
        """
        :param int channel: selected channel
        :param str ONorOFF: 'ON' or 'OFF'
        :return:
        """
        selected_ch = 'smu' + self.ch_map[channel]
        self.device.write(selected_ch + '.source.output=' + selected_ch + '.OUTPUT_' + ONorOFF)

    def set_voltage(self, channel, voltage):
        """
        Set the output voltage of a specified channel
        :param int channel: selected channel: 1,2 (represents A,B)
        :param float voltage: output voltage
        :return:
        """
        if self.safety[channel - 1] == 0:
            warn("Compliance limit for this channel is not set. Run set_limit first to protect your circuit",
                 stacklevel=2)
            return -1
        selected_ch = 'smu' + self.ch_map[channel]
        self.device.write(selected_ch + '.source.func = ' + selected_ch + '.OUTPUT_DCVOLTS')
        self.device.write(selected_ch + '.source.levelv = ' + str(voltage))
        self.device.write('display.' + selected_ch + '.measure.func = display.MEASURE_DCAMPS')

    def set_current(self, channel, current):
        """
        Set the output current of a specified channel
        :param int channel: selected channel: 1,2 (represents A,B)
        :param float current: output current
        :return:
        """
        if self.safety[channel - 1] == 0:
            warn("Compliance limit for this channel is not set. Run set_limit first to protect your circuit",
                 stacklevel=2)
            return -1
        selected_ch = 'smu' + self.ch_map[channel]
        self.device.write(selected_ch + '.source.func = ' + selected_ch + '.OUTPUT_DCAMPS')
        self.device.write(selected_ch + '.source.leveli = ' + str(current))
        self.device.write('display.' + selected_ch + '.measure.func = display.MEASURE_DCVOLTS')

    def set_limit(self, channel, vol_lim, cur_lim):
        """
        Set the output voltage of a specified channel
        :param int channel: selected channel: 1,2 (represents A,B)
        :param float vol_lim: output voltage. Effective when sourcing current.
        :param float cur_lim: output current lim. Effective when sourcing voltage.
        :return:
        """
        selected_ch = 'smu' + self.ch_map[channel]
        self.device.write(selected_ch + '.source.limitv = ' + str(vol_lim))
        self.device.write(selected_ch + '.source.limiti = ' + str(cur_lim))
        self.safety[channel - 1] = 1

    def get_current_voltage(self, channel):
        """
        :param int channel: selected channel: 1,2 (represents A,B)
        :return: [measured_I, measured_V]
        """
        selected_ch = 'smu' + self.ch_map[channel]
        self.device.write('iReading, vReading = ' + selected_ch + '.measure.iv()')
        current = self.device.query("print(iReading)")
        voltage = self.device.query("print(vReading)")
        return [float(current), float(voltage)]

    def release_frontPanel(self):
        time.sleep(0.1)  # wait for SMU. Could not find a command to ask SMU if it's busy or not
        self.device.clear()  # release the front panel and display channel output in real-time

    """
    import visa
    ps = visa.Instrument("GPIB::Address of your instrument")
    ps.write("smua.source.levelv=10")
    ps.write("smua.source.output=smua.OUTPUT_ON")
    ps.write("currenta, voltagea = smua.measure.iv()")
    ps.write("smua.source.output=smua.OUTPUT_OFF")
    current = ps.ask("print(currenta)")
    voltage = ps.ask("print(voltagea)")
    localnode.prompts = 0 
    """


class AFG3000:  # AFG3000 series function generator from Tektronix
    """
    Programmer manual:
    https://download.tek.com/manual/AFG3000-Series-Arbitrary-Function-Generator-Programmer-EN.pdf
    Page 29 shows commands in functional groups which seems very useful.
    The default output impedance is 50 ohms. Be very careful when you don't have a 50ohms termination
        on your PCB. You got double the voltage of what you've set! Boom!
    """

    def __init__(self, instrument_id):
        """
        :param str instrument_id: GPIB address of target device
        """
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(instrument_id)
        print('Initialized  ' + self.device.query('*IDN?'))
        return

    def set_output_state(self, channel, ONorOFF):
        """
        :param int channel: channel number 1 or 2
        :param str ONorOFF: 'ON' or 'OFF'
        """
        self.device.write('OUTPUT' + str(channel) + ':STATE ' + ONorOFF)
        return

    def set_output_vpp(self, channel, amplitude, minV=0, maxV=2.5):
        """
        :param int channel: channel number 1 or 2
        :param float amplitude: amplitude of output signal, referring to 50ohms by default
        :param float minV: minimum output amplitude
        :param float maxV: maximum output amplitude
        :return:
        """
        if amplitude > maxV or amplitude < minV:
            warn("Amplitude exceeds safety boundary. Set another value of minV or maxV",
                 stacklevel=2)
            return -1
        voltage_set = self.device.write(
            'SOURce' + str(channel) + ':VOLTage:LEVel:IMMediate:AMPLitude ' + str(amplitude) + 'VPP')
        return voltage_set

    def set_output_offset(self, channel, offset, minV=0, maxV=2.5):
        """
        :param int channel: channel number 1 or 2
        :param float offset: offset of output signal, referring to 50ohms by default
        :param float minV: minimum output amplitude
        :param float maxV: maximum output amplitude
        :return:
        """
        if offset > maxV or offset < minV:
            warn("offset exceeds safety boundary. Set another value of minV or maxV",
                 stacklevel=2)
            return -1
        voltage_set = self.device.write(
            'SOURce' + str(channel) + ':VOLTage:LEVel:IMMediate:OFFSet ' + str(offset) + 'V')
        return voltage_set

    def set_output_freq(self, channel, freq, unit):
        """
        :param int channel: channel number 1 or 2
        :param float freq: output frequency
        :param str unit: 'Hz' , 'kHz' , 'MHz'
        """
        freq_set = self.device.write('SOURce' + str(channel) + ':FREQuency:FIXed ' + str(freq) + unit)
        return freq_set

    def set_output_shape(self, channel, waveform):
        """
        :param int channel: channel number 1 or 2
        :param str waveform: 'Sine', 'Square', 'Ramp', 'Pulse'
        """
        control = {
            'Sine': 'SINusoid',
            'Square': 'SQUare',
            'Ramp': 'RAMP',
            'Pulse': 'PULSe'
        }
        self.device.write('SOURce' + str(channel) + ':FUNCtion:SHAPe ' + control[waveform])
        return

    def preset_square_wave(self, channel, freq, amplitude, offset):
        self.set_output_offset(channel, offset, 0, 5)
        self.set_output_shape(channel, 'Square')
        self.set_output_vpp(channel, amplitude, 0, 5)
        self.set_output_freq(channel, freq, 'Hz')

    def preset_sine_wave(self, channel, freq, amplitude, offset):
        self.set_output_offset(channel, offset, 0, 5)
        self.set_output_shape(channel, 'Sine')
        self.set_output_vpp(channel, amplitude, 0, 5)
        self.set_output_freq(channel, freq, 'Hz')


def XEM6310_init(bitfile_path):
    """
    This function returns a okCFrontPanel object which contains methods like SetWireInValue(), ReadFromBlockPipeOut().
    Example: xem6310 = XEM6310_init("F:/OneDrive/EEMS/FPGA/Toplevel.bit")
             xem6310.SetWireInValue(0x00, int('01', 2))
             xem6310.UpdateWireIns()
    For detailed information on how to use okCFrontPanel methods, see okCFrontPanel Class Reference.
    Front panel SDK: https://docs.opalkelly.com/fpsdk/introduction/
    Front panel API: https://docs.opalkelly.com/fpsdk/frontpanel-api/
    Examples(very useful!): https://docs.opalkelly.com/frontpanel-sdk-examples/
    okCFrontPanel Class Reference: https://library.opalkelly.com/library/FrontPanelAPI/classokCFrontPanel.html
    :param str bitfile_path: path to your bit file generated by ISE
    :return: okCFrontPanel FPGA: Opal Kelly okCFrontPanel object
    """
    FPGA = ok.okCFrontPanel()  # create xem6310 object
    FPGA.OpenBySerial()  # find connected xem6310
    error = FPGA.ConfigureFPGA(bitfile_path)  # load bitfile
    print(error)
    return FPGA


def list_connected_instrument():
    """
    This function lists all devices connected to PC and print them in form "GPIB_addr    Device_properties"
    """
    rm = pyvisa.ResourceManager()
    instrument_addr = rm.list_resources()
    for addr in instrument_addr:
        instrument_property = rm.open_resource(addr).query('*IDN?')
        print(addr + '  ' + instrument_property + '\n')
    return


def debug():
    pyvisa.log_to_screen()
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    a = KEI2600B('GPIB0::1::INSTR')
    a.set_limit(1, 1, 1e-3)
    a.set_voltage(1, 0.22)
    a.set_output_state(1, 'ON')
    a.release_frontPanel()
    a.set_voltage(1, 0.42)
    a.release_frontPanel()

    print('Connected')


if __name__ == '__main__':
    debug()
