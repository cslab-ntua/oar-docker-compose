Admin FAQ
=========

Release policy
--------------

Since the version 2.2, release numbers are divided into 3 parts:
 - The first represents the design and the implementation used.
 - The second represents a set of OAR functionalities.
 - The third is incremented after bug fixes.

What means the error "Bad configuration option: PermitLocalCommand" when I am using oarsh?
------------------------------------------------------------------------------------------

For security reasons, on the latest OpenSSH releases you are able to execute
a local command when you are connecting to the remote host and we must
deactivate this option because the oarsh wrapper executes the *ssh* command
with oar user privileges.

So if you encounter this error message it means that your OpenSSH does
not know this option and you have to remove it from the oar.conf.
There is a variable named :ref:`OARSH_OPENSSH_DEFAULT_OPTIONS <OARSH_OPENSSH_DEFAULT_OPTIONS>` in oar.conf used by oarsh.
So you have just to remove the not yet implemented option.

How to manage start/stop of the nodes?
--------------------------------------

You have to add a script in /etc/init.d which switches resources of the node
into the "Alive" or "Absent" state.
So when this script is called at boot time, it will change the state into
"Alive". And when it is called at halt time, it will change into "Absent".

There are two ways to perform this action:

 1. Install OAR "oar-libs" part on all nodes. Thus you will be able to launch
    the command :doc:`commands/oarnodesetting` (be careful to right configure "oar.conf" with
    database login and password AND to allow network connections on this
    database).
    So you can execute::

        oarnodesetting -s Alive -h node_hostname
            or
        oarnodesetting -s Absent -h node_hostname

 2. You do not want to install anything else on each node. So you have to
    enable oar user to connect to the server via ssh (for security you
    can use another SSH key with restrictions on the command that oar can
    launch with this one). Thus you will have in your init script
    something like::

        sudo -u oar ssh oar-server "oarnodesetting -s Alive -h node_hostname"
            or
        sudo -u oar ssh oar-server "oarnodesetting -s Absent -h node_hostname"

    In this case, further OAR software upgrade will be more painless.

Take a look in "/etc/default/oar-node" for Debian packaging and in
"/etc/sysconfig/oar-node" for redhat.

How can I manage scheduling queues?
-----------------------------------
see :doc:`commands/oarnotify`.

How can I handle licence tokens?
--------------------------------
There are 2 ways to handle licence tokens:
  - by defining licence resources into OAR (like cores).
  - by calling external scripts that gives the number of free licences.

Defining licence resources into OAR
___________________________________

This approach is useful when everything is done inside the cluster (no
interaction with the outside).

OAR does not manage resources with an empty "network_address". So you can
define resources that are not linked with a real node.

So the steps to configure OAR with the possibility to reserve licences (or
whatever you want that are other notions):

 1. Add a new field in the table :ref:`database-resources-anchor` to specify the licence name.
    ::

        oarproperty -a licence -c

 2. Add your licence name resources with :doc:`commands/oarnodesetting`::

        oarnodesetting -a -h "" -p type=mathlab -p licence=l1
        oarnodesetting -a -h "" -p type=mathlab -p licence=l2
        oarnodesetting -a -h "" -p type=fluent -p licence=l1
        ...

After this configuration, users can perform submissions like
::

    oarsub -I -l "/switch=2/nodes=10+{type='mathlab'}/licence=2"

So users ask OAR to give them some other resource types but nothing blocks
their program to take more licences than they asked. So the users have to
really take care to define the right amount of licences that theirs jobs will
use.

Calling an external script
__________________________

This approach is useful when the cluster processes will use the same licence
servers than other clusters or other computers. So you can't know in advance when
another computer outside the cluster will use the tokens (like the slots for a
proprietary software).

So the only way to handle this situation is to tell the OAR scheduler how many
tokens are free each times. And so it can try to schedule the job that asked
some tokens.

This is not a perfect solution but it works most of the time.

To configure this feature, you have to:

 1. Write a script that displays on the STDOUT the number free tokens.

 2. Edit /etc/oar/oar.conf on the OAR server and change the value of
    SCHEDULER_TOKEN_SCRIPTS; for example::

        SCHEDULER_TOKEN_SCRIPTS="{ fluent => '/usr/local/bin/check_fluent.sh' }"

Then the users will be able to submit jobs like::

    oarsub -l nodes=1/core=12 -t token:fluent=12 ./script.sh

How can I handle multiple clusters with one OAR?
------------------------------------------------
These are the steps to follow:

 1. create a resource property to identify the corresponding cluster (like
    "cluster")::

        oarproperty -a cluster

    (you can see this new property when you use oarnodes)

 2. with :doc:`commands/oarnodesetting` you have to fill this field for all resources; for
    example::

        oarnodesetting -h node42.cluster1.com -p cluster=1
        oarnodesetting -h node43.cluster1.com -p cluster=1
        oarnodesetting -h node2.cluster2.com -p cluster=2
        ...

 3. Then you have to restrict properties for new job type.
    So an admission rule performs this job (you can insert this new rule with
    the :doc:`commands/oaradmissionrules` command)::

        my $cluster_constraint = 0;
        if (grep(/^cluster1$/, @{$type_list})){
            $cluster_constraint = 1;
        }elsif (grep(/^cluster2$/, @{$type_list})){
            $cluster_constraint = 2;
        }
        if ($cluster_constraint > 0){
            if ($jobproperties ne ""){
                $jobproperties = "($jobproperties) AND cluster = $cluster_constraint";
            }else{
                $jobproperties = "cluster = $cluster_constraint";
            }
            print("[ADMISSION RULE] Added automatically cluster resource constraint\n");
        }

 4. Edit the admission rule which checks the right job types and add
    "cluster1" and "cluster2" in.

So when you will use oarsub to submit a "cluster2" job type only resources
with the property "cluster=2" is used. This is the same when you will use the
"cluster1" type. For example::

    oarsub -I -t cluster2
    #is equivalent to
    oarsub -I -p "cluster = 2"

How to configure a more ecological cluster (or how to make some power consumption economies)?
---------------------------------------------------------------------------------------------

This feature can be performed with the `Dynamic nodes coupling features`.

First you have to make sure that you have a command to wake up your nodes.
. For example you can use the ipmitool tool to communicate with the
management boards of the computers.

If you want to enable a node to be woke up the next 12 hours::
    ((DATE=$(date +%s)+3600*12))
    oarnodesetting -h host_name -p available_upto=$DATE

Otherwise you can disable the wake up of nodes (but not the halt) by::

    oarnodesetting -h host_name -p available_upto=1

If you want to disable the halt on a node (but not the wakeup)::

    oarnodesetting -h host_name -p available_upto=2147483647

2147483647 = 2^31 - 1 : we take this value as infinite and it is used to
disable the halt mechanism.

And if you want to disable the halt and the wakeup::

    oarnodesetting -h host_name -p available_upto=0

Your :ref:`SCHEDULER_NODE_MANAGER_WAKE_UP_CMD <SCHEDULER_NODE_MANAGER_WAKE_UP_CMD>` must be a script that reads node
names and translate them into the right wake up commands.

So with the right OAR and node configurations you can optimize the power
consumption of your cluster (and your air conditioning infrastructure)
without drawback for the users.

Take a look at your cluster occupation and your electricity bill to know if it
could be interesting for you ;-)

How to enable jobs to connect to the frontales from the nodes using oarsh?
--------------------------------------------------------------------------
First you have to install the node part of OAR on the wanted nodes.

After that you have to register the frontales into the database using
oarnodesetting with the "frontal" (for example) type and assigned the desired
cpus into the cpuset field; for example::

    oarnodesetting -a -h frontal1 -p type=frontal -p cpuset=0
    oarnodesetting -a -h frontal1 -p type=frontal -p cpuset=1
    oarnodesetting -a -h frontal2 -p type=frontal -p cpuset=0
    ...

Thus you will be able to see resources identifier of these resources with
oarnodes; try to type::

    oarnodes --sql "type='frontal'"

Then put this type name (here "frontal") into the :doc:`oar.conf <configuration>` file on the OAR
server into the tag :ref:`SCHEDULER_NODE_MANAGER_WAKE_UP_CMD <SCHEDULER_RESOURCES_ALWAYS_ASSIGNED_TYPE>`.

Notes:
 - if one of these resources become "Suspected" then the scheduling will
   stop.
 - you can disable this feature with :doc:`commands/oarnodesetting` and put these resources
   into the "Absent" state.

A job remains in the "Finishing" state, what can I do?
------------------------------------------------------
If you have waited more than a couple of minutes (30mn for example) then
something wrong occurred (frontal has crashed, out of memory, ...).

So you are able to turn manually a job into the "Error" state by typing in
the OAR install directory with the root user (example with a bash shell)::

    export OARCONFFILE=/etc/oar/oar.conf
    perl -e 'use OAR::IO; $db = OAR::IO::connect(); OAR::IO::set_job_state($db,42,"Error")'

(Replace 42 by your job identifier)

Since OAR 2.5.3, you can directly use the command:
::

    oardel --force-terminate-finishing-job 42

How to activate the memory management on nodes ?
------------------------------------------------

OAR job resources manager is reponsible for setting up the nodes of a job. Among all 
required steps for that setup, one is to configure the cgroups of the job, in particular
the memory cgroup if it is enabled.

To enable the memory cgroup on some Linux distributions (e.g. Debian), it is necessary to
pass a parameter to the kernel command line (in the boot loader configuration).

For grub on a Debian system, edit /etc/default/grub, and set::

    GRUB_CMDLINE_LINUX_DEFAULT="cgroup_enable=memory"

Once the node is rebooted, check that is indeed appear in ::

    cat /proc/cmdline

and "memory" should appear in ::

    cat /proc/cgroups

Then you just need to set in /etc/oar/job_resource_manager.pl (or the file set in oar.conf for the job resource manager)::

    my $ENABLE_MEMCG = "YES";

The the memory usage of the job is given by the the files::

    /dev/oar_cgroups_links/memory/oar/USERNAME_JOBID/memory.max_usage_in_bytes
    
    /dev/oar_cgroups_links/memory/oar/USERNAME_JOBID/memory.limit_in_bytes
 
The first file tells the maximum amount of memory used by all the processes of the job.
So if "max_usage_in_bytes > limit_in_bytes" then swap was used.


What are the differences with OAR2 ?
------------------------------------

.. list-table:: OAR2 / OAR3 Features comparison
    :widths: 25 25 25
    :header-rows: 1

    * - Feature
      - OAR2
      - OAR3
    * - Programming langage
      - Perl
      - Python (and perl)
    * - Batch and Interactive jobs
      - ✅
      - ✅
    * - Advance Reservation
      - ✅
      - ✅
    * - Admission rules
      - | ✅
        | (in perl)
      - | ✅
        | (in python)
    * - Walltime (with oarwalltime)
      - ✅
      - ✅
    * - Matching of resources (job/node properties)
      - ✅
      - ✅
    * - Hold and resume jobs
      - ✅
      - ?
    * - | Multi-schedulers support
        | (simple fifo and fifo with matching)
      - ✅
      - ✅
    * - Backfilling
      - ✅
      - ✅
    * - First-Fit Scheduler with matching resource
      - ✅
      - ✅
    * - Multi-queues with priority
      - ✅
      - ✅
    * - Best-effort queues (for exploiting idle resources)
      - ✅
      - ✅
    * - Check compute nodes before launching
      - ✅
      - ✅
    * - Epilogue/Prologue scripts
      - ✅
      - ✅
    * - | Jobs and resources
        | visualization tools (Monika, Drawgantt)
      - ✅
      - ✅
    * - No Daemon on compute nodes
      - ✅
      - ✅
    * - | SSH based remote execution protocols
        | (managed by TakTuk)
      - ✅
      - ✅
    * - Dynamic insertion/deletion of compute node
      - ✅
      - ✅
    * - Logging
      - ✅
      - ✅
    * - | On demand OS deployment
        | support with Kadeploy3 coupling
      - ✅
      - ✅
    * - Grid computing support with Cigri
      - ✅
      - ✅
    * - Unit test and coverage
      - ❌
      - | |build|
        | |coverage|

.. |coverage| image:: http://codecov.io/github/oar-team/oar3/coverage.svg?branch=master
    :target: http://codecov.io/github/oar-team/oar3?branch=master
    :alt: Coverage Status

.. |build| image:: https://github.com/oar-team/oar3/actions/workflows/run-tests.yml/badge.svg
    :target: https://github.com/oar-team/oar3/actions/workflows/run-tests.yml/badge.svg
    :alt: Build Status
