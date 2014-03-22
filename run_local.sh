#!/bin/sh
# Script to run a secondary version of the SR script when the main script fails:
# acronjob in acrontab jartieda
# 38 0,6,12,18 * * * lxplus ssh vocms202 /afs/cern.ch/user/j/jartieda/SiteSupportFiles/SiteReadiness/run_local.sh &> /dev/null
location=$HOME/SiteSupportFiles/SiteReadiness
webdir=$HOME/www/SR
webofficial=/afs/cern.ch/cms/LCG/www/sreadiness/SiteReadiness
link=http://cms-site-readiness.web.cern.ch/cms-site-readiness

cd $location

# fixing access
echo "exporting KEY and CERT"
export X509_USER_CERT=/data/certs/servicecert.pem
export X509_USER_KEY=/data/certs/servicekey.pem

# python script
./SiteReadiness.py -p $webdir -u $link
# $webdir: output location
# $link: address to use inside files for output links

# copy output files to web location
cp -a $webdir/. $webofficial/
echo "*** All copies completed ***"