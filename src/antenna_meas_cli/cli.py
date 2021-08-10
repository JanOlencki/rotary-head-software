import pyvisa
import click
import time
from vna_anritsu_MS20xxC_api import vna_api
from rotary_table_api import rotary_table_api as rt_api
from rotary_table_api import rotary_table_messages as rt_msg
import skrf as rf
import matplotlib
from matplotlib import pyplot as plt
import numpy as np

@click.command()
def list_devices():
    rm = pyvisa.ResourceManager()
    click.secho("# Note that not all ports may be listed")
    click.secho("# VISA instruments", bold=True)
    instruments = vna_api.list_visa_instruments(rm)
    for inst_name in instruments:
        idn = vna_api.get_instrument_idn(rm, inst_name)
        click.echo(inst_name + "\t", nl=False)
        if vna_api.is_instrument_supported(idn):
            click.secho(idn, fg="green")
        else:
            click.echo(idn)

    click.secho("# Rotary tables", bold=True)
    for port_name, port_info in rt_api.list_com_ports().items():
        if rt_api.is_com_port_valid(port_info):
            click.secho(port_name, fg="green")
        else:
            click.echo(port_name)

def filename_from_angle_n_s2pname(filename: str, angle: float, angle_step:float = None) -> str:
    precision = None
    if angle_step is None or angle_step != round(angle_step, 0):
        precision = 3
    angle_str = str(round(angle, precision)).replace(".", "#")
    return f"{filename}_{angle_str}deg"

@click.command()
@click.option("--rt-port", required=True, help="Rotary table controller COM port")
@click.option("--rt-id", required=True, type=int, help="Rotary table ID")
@click.option("--vna-name", required=True, help="VNA VISA resource name")
@click.option("--s2p-name", required=True, type=click.Path(exists=False), help="S2P output filename, extension and angle suffix will be automatically added")
@click.option("--s2p-dir", required=False, type=click.Path(exists=False), help="S2P output directory")
@click.option("--speed", default=5, show_default=True, type=float, help="Rotational speed in RPM")
@click.option("--angle-step", default=5, show_default=True, type=float, help="Rotary table will be rotated by angle step between measures. Rotary table rotates 360deg, but don't made measurement after returning home position.")
@click.option("--f-show", multiple=True, type=float, help="Show live plot for given frequencies, GUI may be blocked and works unstable")
@click.option("--rs-converter", is_flag=True)
def meas(rt_port, rt_id, vna_name, s2p_name, s2p_dir, speed, angle_step, f_show, rs_converter):
    rt = rt_api.RotaryTable(rt_port, rs_converter)
    visa_rm = pyvisa.ResourceManager()
    vna = vna_api.VNA(visa_rm, vna_name)

    if not rs_converter:
        resp = rt.send_request(rt_msg.RequestGetConverterStatus(rt_api.CONTROLLER_ADDRESS))      
        click.echo("Controller voltage = ", nl=False)
        volt_fg = "green" if resp.is_voltage_OK else "red"
        click.secho(f"{resp.voltage:2.2f} V", fg=volt_fg)
        if not resp.is_voltage_OK:
            click.secho("Inncorrect supply voltage! Connect USB power source that support USB Quick Charge 2.0 with 12V output voltage.", fg="red")
            return
    rt.send_request(rt_msg.RequestDisable(rt_id))
    click.pause("Rotate antenna to home position by hands and press any key to continue...")
    rt.send_request(rt_msg.RequestHalt(rt_id))
    
    time.sleep(0.1)
    rt.send_request(rt_msg.RequestSetHome(rt_id))
    vna.set_traces_as_s2p()
    vna.set_is_sweep_continuous(False)

    matplotlib.rcParams['toolbar'] = 'None' 
    fig, ax = plt.subplots()
    plots = []
    plots_data = []
    if len(f_show) > 0:
        ax.set_ylim(-100, 0)
        ax.set_xlim(0, 360)        
        ax.set_ylabel("S_21 (dB)")
        ax.set_xlabel("Angle (degrees)")
        for f in f_show:
            line = ax.plot([],[])[0]
            line.set_label(f"f={f:e}")
            plots.append(line)
            plots_data.append([])
        ax.legend()
        fig.canvas.draw()
        plt.show(block=False)
    angle_points = np.arange(0, 360, angle_step)
    try:
        with click.progressbar(angle_points, label="Measuring in progress",
            show_eta=True, show_pos=True) as bar:
            for angle in bar:
                rt.send_request(rt_msg.RequestRotate(rt_id, angle, speed))
                while(rt.send_request(rt_msg.RequestGetStatus(rt_id)).is_rotating):
                    time.sleep(0.2)
                time.sleep(0.5)
                s2p = vna_single_measure(vna)
                s2p.comments = f"angle={angle:f}deg"
                filename = filename_from_angle_n_s2pname(s2p_name, angle, angle_step)                
                s2p.write_touchstone(filename, s2p_dir, skrf_comment=False)
                if len(f_show) > 0:
                    for i in range(len(f_show)):
                        s21db = 20*np.log10(np.abs(s2p.s[np.abs(s2p.f - f_show[i]).argmin()][1,0]))                        
                        plots_data[i].append(s21db)
                        plots[i].set_data(angle_points[0:len(plots_data[i])], plots_data[i])
                    fig.canvas.draw()
                    fig.canvas.flush_events()

        rt.send_request(rt_msg.RequestRotate(rt_id, 0, speed))
        while(rt.send_request(rt_msg.RequestGetStatus(rt_id)).is_rotating):
            time.sleep(0.2)
    except KeyboardInterrupt as err:
        resp = rt.send_request(rt_msg.RequestHalt(rt_id))
        click.secho("Halting rotary table...")
        time.sleep(1)
        resp = rt.send_request(rt_msg.RequestDisable(rt_id))
        click.secho("Disabling rotary table and exit")
        return
    if len(f_show) > 0:
        plt.draw()
        click.pause()

@click.command()
@click.option("--vna-name", required=True, help="VNA VISA resource name")
def vna_meas(vna_name):
    visa_rm = pyvisa.ResourceManager()
    vna = vna_api.VNA(visa_rm, vna_name)
    vna.set_traces_as_s2p()
    vna.set_is_sweep_continuous(False)
    vna.start_single_sweep_await()    
    s2p = vna.get_traces_data_as_s2p()
    s2p.plot_s_db()
    plt.show()
    click.pause()
    vna.set_is_sweep_continuous(True)

def vna_single_measure(vna: vna_api.VNA, test_data=False) -> rf.Network:
    if not test_data:
        vna.start_single_sweep_await()
        return vna.get_traces_data_as_s2p()
    else:
        time.sleep(1)
        freq = rf.Frequency(1, 10, 101, 'ghz')
        s = np.random.rand(101, 2, 2) + 1j*np.random.rand(101, 2, 2)
        return rf.Network(frequency=freq, s=s*1E-2, name='random values 2-port')

@click.group(name="antenna-meas")
def cli():
    pass
cli.add_command(list_devices)
cli.add_command(meas)
cli.add_command(vna_meas)
if __name__ == "__main__":
    cli()
    