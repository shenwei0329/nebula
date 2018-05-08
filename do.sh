#!/bin/bash
#
#

#  db.create
#  data.init
#  data.create_user
#  data.init_permissions
#  data.init_role
#  data.set_default_alarm_meter
#  db.change_password
#  db.clean
#  db.create_permission
#  db.create_user
#  db.drop
#  db.dump
#  db.set_default_alarm_meter
#  doc.build (doc)
#  i18n.compile_catalog
#  i18n.extract_messages
#  i18n.init_catalog
#  i18n.refresh_catalog (i18n)
#  i18n.update_catalog
#  quota.commit
#  quota.get_by_user
#  quota.get_user_quotas
#  quota.reserve
#  quota.rollback
#  quota.test_compute
#  server.web

echo "Starting ... ..."

nohup inv server > log/server.log 2>&1 &

#invoke server &
#  server.central
#sleep 5
#invoke server.flower &
#sleep 5
#invoke server.missions &
#sleep 5
#invoke server.notification &

echo "Done."

#  server.testweb (server)
#  test.all (test)
#  test.models
#  test.views
#
# eof
#
