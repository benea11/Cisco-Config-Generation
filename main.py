from openpyxl import load_workbook
import confparser
from jinja2 import Template


def main(core_file, rack_port_xl, excluded_svi_lst):
    old_inventory, inventory_matrix = workbook_reader(input=rack_port_xl)
    nac_svi = svi_discovery(core_file, excluded_svi_lst)

    old_config = config_parse("CSW.log")

    for switch in old_inventory:
        destination = inventory_matrix[switch["old_sw_name"]]
        f = open(str(destination) + ".txt", "a")
        port = 1
        while port < switch["capacity"] + 1:
            stack_member = switch[port].split("/")[0]
            destination_interface = switch[port].split("/")[1]
            interface_syntax = str(stack_member) + "/0/" + str(destination_interface)
            f.write("interface gig" + interface_syntax + "\n")
            matching_values = [value for key, value in old_config["interface"].items() if
                               interface_syntax.lower() in key.lower()]
            """try:
                f.write(str(matching_values[0]["mode"]) + "\n")
            except:
                f.write(str(matching_values) + "\n")"""

            port += 1


def svi_discovery(core_sw, excluded_svi_lst):
    output = []
    core_config = config_parse(core_sw)
    for interface in core_config['interface']:
        if 'Vlan' in interface and not 'shutdown' in core_config['interface'][interface]:
            if core_config['interface'][interface]['ipv4']:
                subnet_mask = int(core_config['interface'][interface]['ipv4'].split('/')[1])
            else:
                print(interface, 'No ip address configured on this svi, and it is not shutdown')
            if subnet_mask and subnet_mask < 28:
                target_interface = interface.split("n", 1)
                output.append(target_interface[1])
    output = list(set(output) - set(excluded_svi_lst))
    return output


def config_parse(file):
    dissector = confparser.Dissector.from_file('ios.yaml')
    return dissector.parse_file(file)


def workbook_reader(input):
    wb = load_workbook(filename=input, data_only=True)
    sheet_name = wb.sheetnames[index_containing_substring(wb.sheetnames, "availability")]
    sheet = wb[sheet_name]
    e_cell = 1
    old_inventory = []
    inventory_matrix = {}
    while e_cell < 10000:
        output = {}
        if sheet["E" + str(e_cell)].value == "Switch Name: ":
            old_sw = sheet["H" + str(e_cell)].value
            new_sw = sheet["Y" + str(e_cell)].value
            stack_member = sheet["R" + str(e_cell)].value
            output.update({"old_sw_name": old_sw})
            inventory_matrix.update({old_sw: new_sw})
            switch_capacity = 0
            if sheet["D" + str(e_cell + 1)].value == 1:
                switch_capacity = 48
            elif sheet["P" + str(e_cell + 1)].value == 1:
                switch_capacity = 24
            output.update({"capacity": switch_capacity})
            port = "D"
            port_number = 1
            row = 1
            while port_number < switch_capacity + 1:
                if "Z" not in port or "AA" not in port:
                    if not sheet[port + str(e_cell + 2)].value:
                        result = str(stack_member) + "/" + str(port_number)
                    if sheet[port + str(e_cell + 2)].value:
                        result = sheet[port + str(e_cell + 2)].value

                    output.update({
                        port_number: result
                    })
                    port_number += 2
                if port == "AA":
                    if port_number < switch_capacity + 1:
                        if not sheet[port + str(e_cell + 2)].value:
                            result = str(stack_member) + "/" + str(port_number)
                        if sheet[port + str(e_cell + 2)].value:
                            result = sheet[port + str(e_cell + 2)].value

                        output.update({
                            port_number: result
                        })
                    e_cell += 1
                    port = "D"
                    port_number = 2
                    if row == 1:
                        row = 2
                    elif row == 2:
                        port_number = 100
                else:
                    port = chr(ord(port) + 1)
                if port == "Z":
                    if not sheet[port + str(e_cell + 2)].value:
                        result = str(stack_member) + "/" + str(port_number)
                    if sheet[port + str(e_cell + 2)].value:
                        result = sheet[port + str(e_cell + 2)].value

                    output.update({
                        port_number: result
                    })
                    port_number += 2
                    port = "AA"

            e_cell += 1
            old_inventory.append(output)
        else:
            e_cell += 1
    return old_inventory, inventory_matrix


def index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return -1


if __name__ == "__main__":
    excluded_svi_lst = [2]
    core_file = "CSW.log"
    rack_port_xl = "input.xlsx"
    main(core_file, rack_port_xl, excluded_svi_lst)
