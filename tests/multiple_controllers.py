"""
Basic protocol and dataplane test cases

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

Current Assumptions:

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

import sys
import logging

import trace

import unittest

import oftest.match as match
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.instruction as instruction
import oftest.parse as parse

import testutils
import ipaddr

#@var basic_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
basic_port_map = None
#@var basic_logger Local logger object
basic_logger = None
#@var basic_config Local copy of global configuration data
basic_config = None

test_prio = {}

IPV4_ETHERTYPE = 0x0800
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_MPLS = 0x8847
TCP_PROTOCOL = 0x6
UDP_PROTOCOL = 0x11

def test_set_init(config):
    """
    Set up function for basic test classes

    @param config The configuration dictionary; see oft
    """

    global basic_port_map
    global basic_logger
    global basic_config

    basic_logger = logging.getLogger("basic")
    basic_logger.info("Initializing test set")
    basic_port_map = config["port_map"]
    basic_config = config

global current_generation_id 
current_generation_id = 1

def get_new_generation_id():
    global current_generation_id
    current_generation_id += 1
    return current_generation_id

class MultiProtocol(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    def sig_handler(self, v1, v2):
        basic_logger.critical("Received interrupt signal; exiting")
        print "Received interrupt signal; exiting"
        self.clean_shutdown = False
        self.tearDown()
        sys.exit(1)

    def setUp(self):
        self.logger = basic_logger
        self.config = basic_config
        #signal.signal(signal.SIGINT, self.sig_handler)
        basic_logger.info("** START TEST CASE " + str(self))
        self.controller = controller.Controller(
            host=basic_config["controller_host"],
            port=basic_config["controller_port"])
        self.controller.generation_id = 1
        self.controller_sec = controller.Controller(
            host=basic_config["controller_slave_host"],
            port=basic_config["controller_slave_port"])
        self.controller_sec.generation_id = 2
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        self.controller.start()
        self.controller_sec.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)
        self.controller_sec.connect(timeout=20)
        if not self.controller.active or not self.controller_sec.active:
            print "Controller startup failed; exiting"
            sys.exit(1)
        basic_logger.info("Connected " + str(self.controller.switch_addr))

    def tearDown(self):
        basic_logger.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        self.controller_sec.shutdown()
        #@todo Review if join should be done on clean_shutdown
        if self.clean_shutdown:
            self.controller.join()
            self.controller_sec.join()

    def runTest(self):
        # Just a simple sanity check as illustration
        basic_logger.info("Running simple proto test")
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')

    def assertTrue(self, cond, msg):
        if not cond:
            basic_logger.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

test_prio["MultiProtocol"] = 1

class RoleRequest(MultiProtocol):
    """
    Role request message with both controllers     
    """
    def runTest(self):
        request = message.role_request()
        request.generation_id = get_new_generation_id()
        response, _ = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        # print "Controller SEC"
        # print request.show()
        # print response.show()


class RoleRequestMaster(MultiProtocol):
    """
    Role request message with both controllers     
    """
    def runTest(self):
        request = message.role_request()
        request.generation_id = get_new_generation_id()
        request.role = ofp.OFPCR_ROLE_MASTER
        response, _ = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        self.assertEqual(response.role, ofp.OFPCR_ROLE_MASTER,
                     'response\'s role is not Master')
        # print "Controller"
        # print request.show()
        # print response.show()


        request = message.role_request()
        request.generation_id = get_new_generation_id()
        response, _ = self.controller_sec.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        self.assertTrue((response.role != ofp.OFPCR_ROLE_MASTER),
                     'response\'s role is not Master')
        # print "Controller SEC"
        # print request.show()
        # print response.show()

        request = message.role_request()
        request.generation_id = get_new_generation_id()
        request.role = ofp.OFPCR_ROLE_MASTER
        response, _ = self.controller_sec.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        self.assertEqual(response.role, ofp.OFPCR_ROLE_MASTER,
                     'response\'s role is not Master')
        # print "Controller SEC"
        # print request.show()
        # print response.show()

        request = message.role_request()
        request.generation_id = get_new_generation_id()
        response, _ = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        self.assertEqual(response.role, ofp.OFPCR_ROLE_SLAVE,
                     'response\'s role is not Slave')
        # print "Controller"
        # print request.show()
        # print response.show()

        request = message.role_request()
        request.generation_id = get_new_generation_id()
        response, _ = self.controller_sec.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ROLE_REPLY,
                     'response is not role_reply')
        self.assertEqual(response.role, ofp.OFPCR_ROLE_MASTER,
                     'response\'s role is not Master')
        # print "Controller SEC"
        # print request.show()
        # print response.show()



# class SimpleDataPlane(MultiProtocol):
#     """
#     Root class that sets up the controller and dataplane
#     """
#     def setUp(self):
#         MultiProtocol.setUp(self)
#         self.dataplane = dataplane.DataPlane()
#         for of_port, ifname in basic_port_map.items():
#             self.dataplane.port_add(ifname, of_port)

#     def tearDown(self):
#         basic_logger.info("Teardown for simple dataplane test")
#         MultiProtocol.tearDown(self)
#         self.dataplane.kill(join_threads=self.clean_shutdown)
#         basic_logger.info("Teardown done")

#     def runTest(self):
#         self.assertTrue(self.controller.switch_socket is not None,
#                         str(self) + 'No connection to switch')
#         # self.dataplane.show()
#         # Would like an assert that checks the data plane

# class DataPlaneOnly(unittest.TestCase):
#     """
#     Root class that sets up only the dataplane
#     """

#     def sig_handler(self, v1, v2):
#         basic_logger.critical("Received interrupt signal; exiting")
#         print "Received interrupt signal; exiting"
#         self.clean_shutdown = False
#         self.tearDown()
#         sys.exit(1)

#     def setUp(self):
#         self.clean_shutdown = False
#         self.logger = basic_logger
#         self.config = basic_config
#         #signal.signal(signal.SIGINT, self.sig_handler)
#         basic_logger.info("** START DataPlaneOnly CASE " + str(self))
#         self.dataplane = dataplane.DataPlane()
#         for of_port, ifname in basic_port_map.items():
#             self.dataplane.port_add(ifname, of_port)

#     def tearDown(self):
#         basic_logger.info("Teardown for simple dataplane test")
#         self.dataplane.kill(join_threads=self.clean_shutdown)
#         basic_logger.info("Teardown done")

#     def runTest(self):
#         basic_logger.info("DataPlaneOnly")
#         # self.dataplane.show()
#         # Would like an assert that checks the data plane

# class Echo(MultiProtocol):
#     """
#     Test echo response with no data
#     """
#     def runTest(self):
#         testutils.do_echo_request_reply_test(self, self.controller)

# class EchoWithData(MultiProtocol):
#     """
#     Test echo response with short string data
#     """
#     def runTest(self):
#         request = message.echo_request()
#         request.data = 'OpenFlow Will Rule The World'
#         response, _ = self.controller.transact(request)
#         self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
#                          'response is not echo_reply')
#         self.assertEqual(request.header.xid, response.header.xid,
#                          'response xid != request xid')
#         self.assertEqual(request.data, response.data,
#                          'response data does not match request')
#         request = message.echo_request()
#         request.data = 'OpenFlow Will Rule The World Second Controller'
#         response, _ = self.controller_sec.transact(request)
#         self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
#                          'response is not echo_reply')
#         self.assertEqual(request.header.xid, response.header.xid,
#                          'response xid != request xid')
#         self.assertEqual(request.data, response.data,
#                          'response data does not match request')


# class FeaturesRequest(MultiProtocol):
#     """
#     Test features_request to make sure we get a response
    
#     Does NOT test the contents; just that we get a response
#     """
#     def runTest(self):
#         request = message.features_request()
#         response,_ = self.controller.transact(request)
#         self.assertTrue(response,"Got no features_reply to features_request")
#         self.assertEqual(response.header.type, ofp.OFPT_FEATURES_REPLY,
#                          'response is not echo_reply')
#         self.assertTrue(len(response) >= 32, "features_reply too short: %d < 32 " % len(response))
       
# class PacketIn(SimpleDataPlane):
#     """
#     Test packet in function

#     Send a packet to each dataplane port and verify that a packet
#     in message is received from the controller for each
#     """
#     def runTest(self):
#         # Construct packet to send to dataplane
#         # Send packet to dataplane, once to each port
#         # Poll controller with expect message type packet in

#         rc = testutils.delete_all_flows(self.controller, basic_logger)
#         self.assertEqual(rc, 0, "Failed to delete all flows")

#         # Need to insert flow fowarding packets to the controller!!!
#         request = message.flow_mod()
#         request.match.type = ofp.OFPMT_OXM
#         eth_type = match.eth_type(IPV4_ETHERTYPE)
#         eth_dst = match.eth_dst(parse.parse_mac("00:01:02:03:04:05"))
#         ipv6_src = match.ipv4_src(ipaddr.IPv4Address('192.168.0.1'))
        
#         request.match_fields.tlvs.append(eth_type)
#         request.match_fields.tlvs.append(eth_dst)
#         request.match_fields.tlvs.append(ipv6_src)
#         act = action.action_output()
#         act.port = ofp.OFPP_CONTROLLER
#         act.max_len = ofp.OFPCML_NO_BUFFER
#         inst = instruction.instruction_apply_actions()
#         inst.actions.add(act)
#         request.instructions.add(inst)
#         request.buffer_id = 0xffffffff
        
#         request.priority = 1000
#         basic_logger.debug("Adding flow ")

#         rv = self.controller.message_send(request)
#         self.assertTrue(rv != -1, "Failed to insert test flow")
        
#         for of_port in basic_port_map.keys():
#             basic_logger.info("PKT IN test, port " + str(of_port))
#             pkt = testutils.simple_tcp_packet(dl_dst='00:01:02:03:04:05',ip_src='192.168.0.1')
#             self.dataplane.send(of_port, str(pkt))
#             #@todo Check for unexpected messages?
#             (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)

#             self.assertTrue(response is not None, 
#                             'Packet in message not received on port ' + 
#                             str(of_port))
#             if str(pkt) != response.data:
#                 basic_logger.debug("pkt  len " + str(len(str(pkt))) +
#                                    ": " + str(pkt))
#                 basic_logger.debug("resp len " + 
#                                    str(len(str(response.data))) + 
#                                    ": " + str(response.data))
#             self.assertEqual(str(pkt), response.data,
#                              'Response packet does not match send packet' +
#                              ' for port ' + str(of_port))

# class PacketOut(SimpleDataPlane):
#     """
#     Test packet out function

#     Send packet out message to controller for each dataplane port and
#     verify the packet appears on the appropriate dataplane port
#     """
#     def runTest(self):
#         # Construct packet to send to dataplane
#         # Send packet to dataplane
#         # Poll controller with expect message type packet in

#         rc = testutils.delete_all_flows(self.controller, basic_logger)
#         self.assertEqual(rc, 0, "Failed to delete all flows")

#         # These will get put into function
#         outpkt = testutils.simple_tcp_packet()
#         of_ports = basic_port_map.keys()
#         of_ports.sort()
#         for dp_port in of_ports:
#             msg = message.packet_out()
#             msg.in_port = ofp.OFPP_CONTROLLER
#             msg.data = str(outpkt)
#             act = action.action_output()
#             act.port = dp_port
#             self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

#             basic_logger.info("PacketOut to: " + str(dp_port))
#             rv = self.controller.message_send(msg)
#             self.assertTrue(rv == 0, "Error sending out message")

#             (of_port, pkt, _) = self.dataplane.poll(timeout=1)

#             self.assertTrue(pkt is not None, 'Packet not received')
#             basic_logger.info("PacketOut: got pkt from " + str(of_port))
#             if of_port is not None:
#                 self.assertEqual(of_port, dp_port, "Unexpected receive port")
#             self.assertEqual(str(outpkt), str(pkt),
#                              'Response packet does not match send packet')

# class FlowRemoveAll(MultiProtocol):
#     """
#     Remove all flows; required for almost all tests 

#     Add a bunch of flows, remove them, and then make sure there are no flows left
#     This is an intentionally naive test to see if the baseline functionality works 
#     and should be a precondition to any more complicated deletion test (e.g., 
#     delete_strict vs. delete)
#     """
#     def runTest(self):
#         basic_logger.info("Running StatsGet")
#         basic_logger.info("Inserting trial flow")
#         # request = message.flow_mod()
#         # request.buffer_id = 0xffffffff
#         # request.match.type = ofp.OFPMT_OXM
#         # eth_type = match.eth_type(IPV4_ETHERTYPE)
#         # request.match_fields.tlvs.append(eth_type)

#         # act = action.action_output()
#         # act.port = ofp.OFPP_CONTROLLER
#         # act.max_len = ofp.OFPCML_NO_BUFFER
#         # inst = instruction.instruction_apply_actions()
#         # inst.actions.add(act)
#         # request.instructions.add(inst)

#         # request.priority = 1000
#         # basic_logger.debug("Adding flow")
#         # rv = self.controller.message_send(request)
#         # self.assertTrue(rv != -1, "Failed to insert test flow " )

#         for i in range(1,5):
#             request = message.flow_mod()
#             request.buffer_id = 0xffffffff
#             request.match.type = ofp.OFPMT_OXM
#             eth_type = match.eth_type(IPV4_ETHERTYPE)
#             request.match_fields.tlvs.append(eth_type)

#             act = action.action_output()
#             act.port = ofp.OFPP_CONTROLLER
#             act.max_len = ofp.OFPCML_NO_BUFFER
#             inst = instruction.instruction_apply_actions()
#             inst.actions.add(act)
#             request.instructions.add(inst)
#             request.priority = i*1000
#             basic_logger.debug("Adding flow %d" % i)
#             rv = self.controller.message_send(request)
#             self.assertTrue(rv != -1, "Failed to insert test flow %d" % i)

#         basic_logger.info("Removing all flows")
#         testutils.delete_all_flows(self.controller, basic_logger)
#         basic_logger.info("Sending flow request")
#         request = message.flow_stats_request()
#         request.out_port = ofp.OFPP_ANY
#         request.out_group = ofp.OFPG_ANY
#         request.table_id = 0xff
#         response, _ = self.controller.transact(request, timeout=2)
#         self.assertTrue(response is not None, "Did not get response")
#         self.assertTrue(isinstance(response,message.flow_stats_reply),"Not a flow_stats_reply")
#         self.assertEqual(len(response.stats),0)
#         basic_logger.debug(response.show())
        
# class FlowStatsGet(MultiProtocol):
#     """
#     Get stats 

#     Simply verify stats get transaction
#     """
#     def runTest(self):

#         basic_logger.info("Running StatsGet")
#         basic_logger.info("Inserting trial flow")
#         request = message.flow_mod()
#         request.buffer_id = 0xffffffff
        
#         rv = self.controller.message_send(request)        
#         self.assertTrue(rv != -1, "Failed to insert test flow")
        
#         basic_logger.info("Sending flow request")
#         response = testutils.flow_stats_get(self)
#         basic_logger.debug(response.show())

# class TableStatsGet(MultiProtocol):
#     """
#     Get table stats 

#     Naively verify that we get a reply
#     do better sanity check of data in stats.TableStats test
#     """
#     def runTest(self):
#         basic_logger.info("Running TableStatsGet")
#         basic_logger.info("Sending table stats request")
#         request = message.table_stats_request()
#         response, _ = self.controller.transact(request, timeout=2)
#         self.assertTrue(response is not None, "Did not get response")
#         basic_logger.debug(response.show())

# class FlowMod(MultiProtocol):
#     """
#     Insert a flow

#     Simple verification of a flow mod transaction
#     """

#     def runTest(self):
#         basic_logger.info("Running " + str(self))
#         request = message.flow_mod()
#         request.buffer_id = 0xffffffff
#         rv = self.controller.message_send(request)
#         self.assertTrue(rv != -1, "Error installing flow mod")

# class PortConfigMod(MultiProtocol):
#     """
#     Modify a bit in port config and verify changed

#     Get the switch configuration, modify the port configuration
#     and write it back; get the config again and verify changed.
#     Then set it back to the way it was.
#     """

#     def runTest(self):
#         basic_logger.info("Running " + str(self))
#         for of_port, _ in basic_port_map.items(): # Grab first port
#             break

#         (_, config, _) = \
#             testutils.port_config_get(self.controller, of_port, basic_logger)
#         self.assertTrue(config is not None, "Did not get port config")

#         basic_logger.debug("No flood bit port " + str(of_port) + " is now " + 
#                            str(config & ofp.OFPPC_NO_PACKET_IN))

#         rv = testutils.port_config_set(self.controller, of_port,
#                              config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN,
#                              basic_logger)
#         self.assertTrue(rv != -1, "Error sending port mod")

#         # Verify change took place with same feature request
#         (_, config2, _) = \
#             testutils.port_config_get(self.controller, of_port, basic_logger)
#         self.assertTrue(config2 is not None, "Did not get port config2")
#         basic_logger.debug("No packet_in bit port " + str(of_port) + " is now " + 
#                            str(config2 & ofp.OFPPC_NO_PACKET_IN))
#         self.assertTrue(config2 & ofp.OFPPC_NO_PACKET_IN !=
#                         config & ofp.OFPPC_NO_PACKET_IN,
#                         "Bit change did not take")
#         # Set it back
#         rv = testutils.port_config_set(self.controller, of_port, config, 
#                              ofp.OFPPC_NO_PACKET_IN, basic_logger)
#         self.assertTrue(rv != -1, "Error sending port mod")
        

# TABLE_MISS_CONTROLLER = 0,    # Send to controller.
# TABLE_MISS_CONTINUE = 1 << 0, #/* Continue to the next table in the
#                                     #   pipeline (OpenFlow 1.0 behavior). */
# TABLE_MISS_DROP = 1 << 1,     #/* Drop the packet. */
# TABLE_MISS_MASK = 3
# def table_config(parent, set_id = 0, mode = None):
#     """
#     Configure table packet handling
#     """
#     if mode is None :
#         return False
#     request = message.flow_mod()
#     request.match.type = ofp.OFPMT_OXM
#     request.buffer_id = 0xffffffff
#     request.table_id = set_id
#     request.priority = 0
#     inst = instruction.instruction_apply_actions()

#     if mode == TABLE_MISS_CONTROLLER:
#         act = action.action_output()
#         act.port = ofp.OFPP_CONTROLLER
#         act.max_len = ofp.OFPCML_NO_BUFFER
#         inst.actions.add(act)
#     elif mode == TABLE_MISS_CONTINUE :
#         inst = instruction.instruction_goto_table()
#         inst.table_id = set_id + 1
#     elif mode == TABLE_MISS_DROP :
#         act = 0
#     else :
#         return False

#     parent.assertTrue(request.instructions.add(inst), "Can't add inst")
#     basic_logger.info("Inserting flow")
#     rv = parent.controller.message_send(request)
#     parent.assertTrue(rv != -1, "Error installing flow mod")
#     testutils.do_barrier(parent.controller)
#     return True

# class TableModConfig(MultiProtocol):
#     """ Simple table modification
    
#     Mostly to make sure the switch correctly responds to these messages.
#     More complicated tests in the multi-tables.py tests
#     """        
#     def runTest(self):
#         basic_logger.info("Running " + str(self))
        
#         rv = table_config(self,1,TABLE_MISS_CONTROLLER)

#         self.assertTrue(rv, "Error sending table_mod")
#         testutils.do_echo_request_reply_test(self, self.controller)
    

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=multiple_controller"