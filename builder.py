'''SET THE QOS INPUT POLICY NAME CORRECTLY BASED ON CUSTOMER REQUIREMENTS'''
import confparser
import time
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='This script is used for generating switch configurations based on existing configs')
    parser.add_argument('--csw', metavar='csw', help='Core Switch Configuration')
    parser.add_argument('--asw', metavar='asw', help='Access Switch Configuration')
    parser.add_argument('--out', metavar='out', help='Output File')
    parser.add_argument('--old-stack', metavar='old-stack',
                        help='Original Stack Number (or line card number)')
    parser.add_argument('--new-stack', metavar='new-stack',
                        help='Destined Stack Number')
    args = parser.parse_args()

    csw_output = config_parse(args.csw)
    asw_output = config_parse(args.asw)

    svi_list = svi_builder(csw_output)

    nonac_template = '''switchport mode access
switchport nonegotiate
no logging event link-status 
cdp enable
no snmp trap link-status
storm-control broadcast level 60.00 50.00
storm-control multicast level 60.00 50.00
storm-control action shutdown
spanning-tree portfast
spanning-tree bpduguard enable
service-policy input QoS
service-policy output 2P6Q3T
'''

    nac_template = '''switchport mode access
switchport nonegotiate
no snmp trap link-status
storm-control broadcast level 60.00 50.00
storm-control multicast level 60.00 50.00
storm-control action shutdown
spanning-tree portfast
service-policy input QoS
service-policy output 2P6Q3T
authentication host-mode multi-auth
authentication open
authentication order dot1x mab
authentication port-control auto
authentication periodic
authentication timer reauthenticate server
authentication timer inactivity server dynamic
mab
dot1x pae authenticator
dot1x timeout tx-period 7
dot1x max-reauth-req 3
'''

    interface_list = interface_builder(asw_output)
    if args.old_stack and args.new_stack:
        for i in interface_list:
            try:
                original_interface = i['original-interface'].split('net')
                original_interface = original_interface[1].split('/')
                if original_interface[0] == args.old_stack:
                    new_interface_number = {
                        'new-interface': "interface GigabitEthernet" + args.old_stack + '/0/' + original_interface[1]
                    }
                    i.update(new_interface_number)

            except:
                continue

    interface_list = config_builder(interface_list, nonac_template, nac_template, svi_list)
    trunk_list = [i for i in interface_list if not (i['mode'] != 'trunk')]
    excluded_list = [i for i in interface_list if (i['mode'] != 'access')]
    excluded_list = [i for i in excluded_list if (i['mode'] != 'trunk')]
    interface_list = [i for i in interface_list if not (i['mode'] != 'access')]

    out_file(interface_list, excluded_list, args.out, svi_list, trunk_list)


def out_file(interface_list, excluded_list, output, svi_list, trunk_list):
    f = open(output, "a")
    f.write('-------------------INFO-------------------' + "\n")
    f.write("\n")
    f.write('The following SVI IDs are configured on the core switch, and are NOT shutdown:' + "\n")
    for i in svi_list:
        f.write(i + ", ")
    f.write('\n')
    f.write('\n------------------------------------------' + "\n")
    f.write("\n")
    f.write('The following interfaces have been excluded.' + "\n")
    f.write('IMPORTANT: The interfaces presented here are based on the old switch config' + "\n")
    f.write('\n')
    for i in excluded_list:
        try:
            if not i['shutdown']:
                f.write(i['original-interface'] + "\n")
                if i['mode']:
                    f.write('Interface Mode:  ' + i['mode'] + '\n')
                    f.write('!\n')
                else:
                    f.write('Interface Mode:  Not defined.. (access/trunk) \n')
                    f.write('\n')
        except KeyError:
            break
    f.write('\n')
    f.write('\n------------------------------------------' + "\n")
    f.write('\n')
    f.write('The following interfaces are trunk interfaces and have been excluded.' + '\n')
    f.write('IMPORTANT: The interfaces presented here are based on the old switch config' + "\n")
    f.write('\n')
    for i in trunk_list:
        try:
            if not i['shutdown']:
                f.write(i['original-interface'] + '\n')
            try:
                if i['channel']['id']:
                    f.write('//Channel group ID:  ' + i['channel']['id'] + '\n')
                    f.write('//Channel mode:  ' + i['channel']['mode'] + '\n')
                else:
                    f.write('//Not a member of a channel group\n')
            except KeyError:
                f.write('Does not belong to a channel group \n')
        except KeyError:
            f.write('\n')
        f.write('\n')
    f.write('\n------------------------------------------' + "\n")
    f.write("\n")
    f.write("\n")
    f.write("\n")
    f.write('------------------CONFIG------------------' + "\n")
    for i in interface_list:
        try:
            if i['shutdown']:
                continue
            f.write(i['new-interface'] + "\n")
            if i['description']:
                f.write('description ' + str(i['description']) + "\n")
            f.write('switchport access vlan ' + str(i['access_vlan']) + "\n")
            if i['voice_vlan']:
                f.write('switchport voice vlan ' + str(i['voice_vlan']) + "\n")
            if i['ps_max']:
                f.write('switchport port-security' + "\n")
                f.write('switchport port-security maximum ' + i['ps_max'] + "\n")
                f.write('switchport port-security violation restrict' + "\n")
                f.write('switchport port-security no logging event link-status' + "\n")
                if i['ps_age']:
                    f.write('switchport port-security aging time ' + i['ps_age'] + "\n")

            if i['dhcp_snoop']:
                f.write('ip dhcp snooping trust' + "\n")
            f.write(i['templated-config'] + "\n")
        except KeyError:
            continue
    for i in trunk_list:
        if i['shutdown']:
            if 'Vlan' not in i['original-interface']:
                try:
                    f.write(i['new-interface'] + '\n')
                    f.write('description --- FREE ---' + '\n')
                    f.write('shutdown' + '\n')
                except KeyError:
                    continue
    for i in excluded_list:
        if i['shutdown']:
            if 'Vlan' not in i['original-interface']:
                try:
                    f.write('interface ' + i['new-interface'] + '\n')
                    f.write('description --- FREE ---' + '\n')
                    f.write('shutdown' + '\n')
                except KeyError:
                    continue
    for i in interface_list:
        if i['shutdown']:
            try:
                f.write(i['new-interface'] + '\n')
                f.write('description --- FREE ---' + '\n')
                f.write('shutdown' + '\n')
            except KeyError:
                continue
    f.close()


def config_builder(interface_list, nonac_template, nac_template, svi_list):
    for i in interface_list:
        if i['original-interface'].count('/') == 1:

            if i['access_vlan'] in svi_list:
                i.update({'templated-config': nac_template})
            else:
                i.update({'templated-config': nonac_template})

        elif i['original-interface'].count('/') > 1:
            interface_number = str(i['original-interface'])
            interface_number = interface_number.split("et", 1)
            interface_number = str(interface_number[1])
            new_interface_number = {
                'new-interface': "interface GigabitEthernet" + str(interface_number)}
            i.update(new_interface_number)
            if i['access_vlan'] in svi_list:
                i.update({'templated-config': nac_template})
            else:
                i.update({'templated-config': nonac_template})
    return interface_list


def interface_builder(asw_output):
    interface_list = []
    for int in asw_output['interface']:
        try:
            description = asw_output['interface'][int]['description']
        except KeyError:
            description = ""
        try:
            access_vlan = asw_output['interface'][int]['access_vlan']
        except KeyError:
            access_vlan = ""
        try:
            voice_vlan = asw_output['interface'][int]['voice_vlan']
        except KeyError:
            voice_vlan = ""
        try:
            mode = asw_output['interface'][int]['mode']
        except KeyError:
            mode = ""
        try:
            ps_max = asw_output['interface'][int]['ps_max']
        except KeyError:
            ps_max = ""
        try:
            ps_aging_time = asw_output['interface'][int]['ps_aging_time']
        except KeyError:
            ps_aging_time = ""
        try:
            dhcp_snooping_trust = asw_output['interface'][int]['dhcp_snooping_trust']
        except KeyError:
            dhcp_snooping_trust = ""
        try:
            status = asw_output['interface'][int]['shutdown']
        except KeyError:
            status = ""
        try:
            channel = asw_output['interface'][int]['channel']
        except KeyError:
            channel = ""
        interface_id = int
        interface_list.append({'original-interface': interface_id,
                               'mode': mode,
                               'description': description,
                               'access_vlan': access_vlan,
                               'voice_vlan': voice_vlan,
                               'ps_max': ps_max,
                               'ps_age': ps_aging_time,
                               'dhcp_snoop': dhcp_snooping_trust,
                               'shutdown': status,
                               'channel': channel})
    return interface_list


def svi_builder(core_config):
    svi_list = []
    for int in core_config['interface']:
        if 'Vlan' in int:
            if 'shutdown' not in core_config['interface'][int]:
                int = int.split("n", 1)
                svi_list.append(int[1])
    excluded_svi = ['10', '12', '2', '50', '51', '52', '53', '61', '290', '295', '425', '601', '604', '605', '610',
                    '685']
    svi_list = list(set(svi_list) - set(excluded_svi))
    return svi_list


def config_parse(file):
    dissector = confparser.Dissector.from_file('ios.yaml')
    return dissector.parse_file(file)


if __name__ == "__main__":
    start_time = time.time()
    main()
    run_time = time.time() - start_time
    print("\n** Configuration Generated")
    print("** Time to run: %s sec" % round(run_time, 3))
