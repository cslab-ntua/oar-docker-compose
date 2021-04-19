#!/bin/bash
set -ue

IFS='.' read DEBIAN_VERSION DEBIAN_VERSION_MINOR < /etc/debian_version

TMPDIR=$(mktemp -d --tmpdir install_oar.XXXXXXXX)
SRCDIR="$TMPDIR/src"

mkdir -p $SRCDIR

on_exit() {
    mountpoint -q $SRCDIR && umount $SRCDIR || true
    rm -rf $TMPDIR
}

trap "{ on_exit; kill 0; }" EXIT

fail() {
    echo $@ 1>&2
    exit 1
}

TARBALL=${1:-http://oar-ftp.imag.fr/oar/2.5/sources/testing/oar-2.5.8.tar.gz}

echo "TARBALL: $TARBALL"

[ -n "$TARBALL" ] || fail "error: You must provide a URL to a OAR tarball"
if [ ! -r "$TARBALL" ]; then
    curl $TARBALL -o $TMPDIR/oar-tarball.tar.gz
    TARBALL=$TMPDIR/oar-tarball.tar.gz
else
    TARBALL="$(readlink -m $TARBALL)"
fi

VERSION=$(tar xfz $TARBALL --wildcards "*/sources/core/common-libs/lib/OAR/Version.pm" --to-command "grep -e 'my \$OARVersion'" | sed -e 's/^[^"]\+"\(.\+\)";$/\1/')

COMMENT="OAR ${VERSION} (tarball)"
tar xf $TARBALL -C $SRCDIR
[ -n "${VERSION}" ] || fail "error: fail to retrieve OAR version"
SRCDIR=$SRCDIR/oar-${VERSION}

# Install OAR server
make -C $SRCDIR PREFIX=/usr/local server-build
make -C $SRCDIR PREFIX=/usr/local server-install
make -C $SRCDIR PREFIX=/usr/local server-setup

# Install OAR user cli (oarnodes, oarstat ...)
make -C $SRCDIR PREFIX=/usr/local user-build
make -C $SRCDIR PREFIX=/usr/local user-install 
make -C $SRCDIR PREFIX=/usr/local user-setup 

# Copy initd scripts
if [ -f /usr/local/share/oar/oar-server/init.d/oar-server ]; then
    cat /usr/local/share/oar/oar-server/init.d/oar-server > /etc/init.d/oar-server
    chmod +x  /etc/init.d/oar-server
fi

if [ -f /usr/local/share/oar/oar-server/default/oar-server ]; then
    cat /usr/local/share/oar/oar-server/default/oar-server > /etc/default/oar-server
fi

if [ -f /usr/local/share/oar/oar-server/job_resource_manager_cgroups.pl ]; then
    ln -sf /usr/local/share/oar/oar-server/job_resource_manager_cgroups.pl /etc/oar/job_resource_manager_cgroups.pl
fi

cp /common/oar2.conf /etc/oar/oar.conf
chown oar:oar /etc/oar/oar.conf
chmod 600 /etc/oar/oar.conf

# OAR SSH KEYS the same for all nodes 
/common/configure_oar_ssh_keys.sh

systemctl enable oar-server
