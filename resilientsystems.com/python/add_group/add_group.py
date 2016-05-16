#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Action Module circuits component to add different users depending on severity"""

from __future__ import print_function
import logging
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent

LOG = logging.getLogger(__name__)

CONFIG_DATA_SECTION = 'addgroup1'


class AddGroupComponent(ResilientComponent):
    """Adds different users and groups depending on an incident's severity"""

    # This component adds different users and groups depending on an incident's severity

    def __init__(self, opts):
        super(AddGroupComponent, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        LOG.debug(self.options)

        # The queue name can be specified in the config file,
        # or default to 'addgroup'
        self.channel = "actions." + self.options.get("queue", "addgroup")

    @handler("add_group")
    def __add__group(self, event, *args, **kwargs):
        # get information about the incident, such as its ID and severity
        incident = event.message["incident"]
        inc_id = incident["id"]

        # Severity code is an id (SELECT field) so we need to find the text label
        # There's a helper function in ResilientComponent for this purpose.
        incident_severity = incident["severity_code"]
        incident_severity_label = self.get_field_label("severity_code", incident_severity)
        LOG.info(incident_severity_label)

        def update_owner(inc):
            """updates the owner, given an incident"""
            # if High severity, make the owner the high_owner
            if incident_severity_label == "High":
                inc["owner_id"] = self.options.get("high_owner")
            # else if Medium severity, make the owner the medium_owner
            elif incident_severity_label == "Medium":
                inc['owner_id'] = self.options.get("medium_owner")
            # else if Low security, make the owner the low_owner
            elif incident_severity_label == "Low":
                inc['owner_id'] = self.options.get("low_owner")
            return inc

        # Update the incident owner
        self.rest_client().get_put("/incidents/"+str(inc_id), update_owner)

        def update_members(inc):
            """updates the members, given an incident"""
            # if High severity, make high_member_1 the only member
            if incident_severity_label == "High":
                inc["members"] = [self.options.get("high_member_1")]
            # else if Medium severity, make medium_member_1 and
            # medium_member_2 the members
            elif incident_severity_label == "Medium":
                inc['members'] = [self.options.get("medium_member_1"),
                                  self.options.get("medium_member_2")]
            # else if Low severity, make low_member_1, low_member_2,
            # and low_member_3 the members
            elif incident_severity_label == "Low":
                inc['members'] = [self.options.get("low_member_1"),
                                  self.options.get("low_member_2"),
                                  self.options.get("low_member_3")]
            return inc

        # Update the incident members
        self.rest_client().get_put("/incidents/" + str(inc_id), update_members)

        status = "Finished adding users to incident {0} due to severity change".format(inc_id)
        yield status
