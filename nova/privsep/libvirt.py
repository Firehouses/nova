# Copyright 2016 Red Hat, Inc
# Copyright 2017 Rackspace Australia
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
libvirt specific routines that use the dac_admin_pctxt to bypass file-system
checks.
"""

import errno
import os

import nova.privsep


@nova.privsep.dac_admin_pctxt.entrypoint
def last_bytes(path, num):
    # NOTE(mikal): this is implemented in this contrived manner because you
    # can't mock a decorator in python (they're loaded at file parse time,
    # and the mock happens later).
    with open(path, 'rb') as f:
        return _last_bytes_inner(f, num)


def _last_bytes_inner(file_like_object, num):
    """Return num bytes from the end of the file, and remaining byte count.

    :param file_like_object: The file to read
    :param num: The number of bytes to return

    :returns: (data, remaining)
    """

    try:
        file_like_object.seek(-num, os.SEEK_END)
    except IOError as e:
        # seek() fails with EINVAL when trying to go before the start of
        # the file. It means that num is larger than the file size, so
        # just go to the start.
        if e.errno == errno.EINVAL:
            file_like_object.seek(0, os.SEEK_SET)
        else:
            raise

    remaining = file_like_object.tell()
    return (file_like_object.read(), remaining)


@nova.privsep.dacnet_admin_pctxt.entrypoint
def enable_hairpin(interface):
    """Enable hairpin mode for a libvirt guest."""
    with open('/sys/class/net/%s/brport/hairpin_mode' % interface, 'w') as f:
        f.write('1')


@nova.privsep.dacnet_admin_pctxt.entrypoint
def disable_multicast_snooping(interface):
    """Disable multicast snooping for a bridge."""
    with open('/sys/class/net/%s/bridge/multicast_snooping' % interface,
              'w') as f:
        f.write('0')


@nova.privsep.dacnet_admin_pctxt.entrypoint
def disable_ipv6(interface):
    """Disable ipv6 for a bridge."""
    with open('/proc/sys/net/ipv6/conf/%s/disable_ipv' % interface, 'w') as f:
        f.write('1')
