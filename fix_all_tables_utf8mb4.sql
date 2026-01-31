-- Convert ALL project tables to utf8mb4 so Persian/UTF-8 text works everywhere.
-- Run once in your database: mysql -u USER -p ufvuikiv_project_manager_db < fix_all_tables_utf8mb4.sql
-- Or: USE ufvuikiv_project_manager_db; then paste the ALTER lines.
-- If a table does not exist (e.g. app not migrated), skip that line or ignore the error.

-- Database default (optional; fix typo: space not tab after db name)
ALTER DATABASE ufvuikiv_project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- accounts
ALTER TABLE accounts_expertprovince CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE accounts_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE accounts_userprovince CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE accounts_user_groups CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE accounts_user_user_permissions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- auth
ALTER TABLE auth_group CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE auth_group_permissions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE auth_permission CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- creator_program
ALTER TABLE creator_program_program CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_program_programrejectioncomment CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_program_programupdatehistory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- creator_project (includes main Project table and subproject-related)
ALTER TABLE creator_project_allocationcreditcash CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_allocationcredittreasury CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_all_project CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_fundingrequest CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_project CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_projectfinancialallocation CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_projectgalleryimage CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_projectrejectioncomment CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_project_projectupdatehistory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- creator_subproject (IMPORTANT: creator_subproject_subproject is required for creating new subprojects)
ALTER TABLE creator_subproject_adjustmentsituationreport CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_documentfile CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_financialdocument CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_payment CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_projectsituation CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_situationreport CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_subproject CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_subprojectgalleryimage CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_subprojectrejectioncomment CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_subproject_subprojectupdatehistory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- creator_review
ALTER TABLE creator_review_projectreview CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE creator_review_subprojectreview CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- session_manager
ALTER TABLE session_manager_sessionlog CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE session_manager_sessionsecurity CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- activity_monitor
ALTER TABLE activity_monitor_activitylog CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_projectchangelog CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_usersession CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_systemevent CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_activitydashboard CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_audittrail CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE activity_monitor_gallerysettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- notifications_sms
ALTER TABLE notifications_sms_smsprovider CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_sms_smssettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_sms_smstemplate CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_sms_smslog CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- notifications (app name notifications, not notifications_sms)
ALTER TABLE notifications_smssettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_rejectionsmssettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_expertremindersmssettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_smslog CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notifications_projectexpertnotification CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- reporter
ALTER TABLE reporter_searchhistory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE reporter_projectreport CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE reporter_subprojectreport CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE reporter_generatedreport CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE reporter_projectfinancialallocation CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- webhooks
ALTER TABLE webhooks_webhookevent CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE webhooks_webhookconfiguration CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- django
ALTER TABLE django_admin_log CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_content_type CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_migrations CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_session CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
