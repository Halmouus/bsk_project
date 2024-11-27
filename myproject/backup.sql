-- MySQL dump 10.13  Distrib 8.0.40, for Linux (x86_64)
--
-- Host: localhost    Database: django_project
-- ------------------------------------------------------
-- Server version	8.0.40-0ubuntu0.20.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add item',7,'add_item'),(26,'Can change item',7,'change_item'),(27,'Can delete item',7,'delete_item'),(28,'Can view item',7,'view_item'),(29,'Can add profile',8,'add_profile'),(30,'Can change profile',8,'change_profile'),(31,'Can delete profile',8,'delete_profile'),(32,'Can view profile',8,'view_profile'),(33,'Can add invoice',9,'add_invoice'),(34,'Can change invoice',9,'change_invoice'),(35,'Can delete invoice',9,'delete_invoice'),(36,'Can view invoice',9,'view_invoice'),(37,'Can add product',10,'add_product'),(38,'Can change product',10,'change_product'),(39,'Can delete product',10,'delete_product'),(40,'Can view product',10,'view_product'),(41,'Can add supplier',11,'add_supplier'),(42,'Can change supplier',11,'change_supplier'),(43,'Can delete supplier',11,'delete_supplier'),(44,'Can view supplier',11,'view_supplier'),(45,'Can add invoice product',12,'add_invoiceproduct'),(46,'Can change invoice product',12,'change_invoiceproduct'),(47,'Can delete invoice product',12,'delete_invoiceproduct'),(48,'Can view invoice product',12,'view_invoiceproduct'),(49,'Can add export record',13,'add_exportrecord'),(50,'Can change export record',13,'change_exportrecord'),(51,'Can delete export record',13,'delete_exportrecord'),(52,'Can view export record',13,'view_exportrecord'),(53,'Can export invoice',9,'can_export_invoice'),(54,'Can unexport invoice',9,'can_unexport_invoice'),(55,'Can add checker',14,'add_checker'),(56,'Can change checker',14,'change_checker'),(57,'Can delete checker',14,'delete_checker'),(58,'Can view checker',14,'view_checker'),(59,'Can add check',15,'add_check'),(60,'Can change check',15,'change_check'),(61,'Can delete check',15,'delete_check'),(62,'Can view check',15,'view_check');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$tCnXBKO4ji2IeXtoPWcr6A$upTiUILRb3KvLmPRrVYw45IHin5iKYRJJnXkFx69NCA=','2024-11-23 07:34:30.149254',1,'codespace','','','javierminimaz@gmail.com',1,1,'2024-11-22 14:01:25.001112'),(2,'pbkdf2_sha256$600000$Oa4gRorihmUXoLU7HvIS03$wG/Jye5b8amNwxMGALG1PCVfIQo22FRMeGXew5jGebo=',NULL,0,'admin','JAVIER','MINIMAZ','javierminimaz@gmail.com',0,1,'2024-11-22 14:04:27.000000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2024-11-22 14:04:28.103525','2','admin',1,'[{\"added\": {}}]',4,1),(2,'2024-11-22 14:05:06.793437','2','admin',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Email address\"]}}]',4,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(15,'testapp','check'),(14,'testapp','checker'),(13,'testapp','exportrecord'),(9,'testapp','invoice'),(12,'testapp','invoiceproduct'),(7,'testapp','item'),(10,'testapp','product'),(8,'testapp','profile'),(11,'testapp','supplier');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-11-22 13:56:40.772438'),(2,'auth','0001_initial','2024-11-22 13:56:41.044553'),(3,'admin','0001_initial','2024-11-22 13:56:41.127391'),(4,'admin','0002_logentry_remove_auto_add','2024-11-22 13:56:41.134217'),(5,'admin','0003_logentry_add_action_flag_choices','2024-11-22 13:56:41.141159'),(6,'contenttypes','0002_remove_content_type_name','2024-11-22 13:56:41.180919'),(7,'auth','0002_alter_permission_name_max_length','2024-11-22 13:56:41.212469'),(8,'auth','0003_alter_user_email_max_length','2024-11-22 13:56:41.231131'),(9,'auth','0004_alter_user_username_opts','2024-11-22 13:56:41.236902'),(10,'auth','0005_alter_user_last_login_null','2024-11-22 13:56:41.264965'),(11,'auth','0006_require_contenttypes_0002','2024-11-22 13:56:41.267891'),(12,'auth','0007_alter_validators_add_error_messages','2024-11-22 13:56:41.274004'),(13,'auth','0008_alter_user_username_max_length','2024-11-22 13:56:41.333960'),(14,'auth','0009_alter_user_last_name_max_length','2024-11-22 13:56:41.401005'),(15,'auth','0010_alter_group_name_max_length','2024-11-22 13:56:41.417695'),(16,'auth','0011_update_proxy_permissions','2024-11-22 13:56:41.423965'),(17,'auth','0012_alter_user_first_name_max_length','2024-11-22 13:56:41.455513'),(18,'sessions','0001_initial','2024-11-22 13:56:41.475859'),(19,'testapp','0001_initial','2024-11-22 13:56:41.488570'),(20,'testapp','0002_item_created_at_item_updated_at_alter_item_id','2024-11-22 13:56:41.535242'),(21,'testapp','0003_profile','2024-11-22 13:56:41.588964'),(22,'testapp','0004_alter_profile_date_of_joining','2024-11-22 13:56:41.612060'),(23,'testapp','0005_invoice_product_supplier_invoiceproduct_and_more','2024-11-22 13:56:41.743413'),(24,'testapp','0006_alter_invoiceproduct_quantity_and_more','2024-11-22 13:56:41.815448'),(25,'testapp','0007_invoice_payment_due_date_invoice_status_and_more','2024-11-22 13:56:41.853452'),(26,'testapp','0008_product_fiscal_label_alter_invoiceproduct_vat_rate_and_more','2024-11-22 13:56:41.877041'),(27,'testapp','0009_remove_invoice_fiscal_label','2024-11-22 13:56:41.892986'),(28,'testapp','0010_invoice_exported_at_exportrecord_and_more','2024-11-22 13:56:42.012740'),(29,'testapp','0011_alter_supplier_name_and_more','2024-11-22 13:56:42.074087'),(30,'testapp','0012_alter_invoice_supplier_alter_invoiceproduct_product','2024-11-22 13:56:42.091419'),(31,'testapp','0013_alter_invoice_options','2024-11-23 07:35:48.850297'),(32,'testapp','0014_checker_check_check_check_amount_cannot_exceed_due','2024-11-23 07:35:48.989726'),(33,'testapp','0015_check_cancellation_reason_check_cancelled_at_and_more','2024-11-23 08:04:55.218428'),(34,'testapp','0016_invoice_payment_status_alter_checker_index','2024-11-26 07:48:59.730161'),(35,'testapp','0017_invoice_original_invoice_invoice_type_and_more','2024-11-26 07:48:59.856651');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('lhdamsjhpg7kn3tnxpgx18eu1xgnpwpc','.eJxVjDsOwjAQBe_iGlm7-LempOcMlr84gGwpTirE3UmkFNC-mXlv5vy6VLeOPLspsQtDdvrdgo_P3HaQHr7dO4-9LfMU-K7wgw5-6ym_rof7d1D9qFutpLRn6QtQxoImUvGgMBhbApWMgKiViIK0tnYjAqSEJAMZYSxAIfb5AsIkNok:1tEkf0:9ulavvhsBSSn008pWODEEYz5e7I99Z3hBdXoWnmTjWU','2024-12-07 07:34:30.155733');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_check`
--

DROP TABLE IF EXISTS `testapp_check`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_check` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `position` varchar(10) NOT NULL,
  `creation_date` date NOT NULL,
  `payment_due` date DEFAULT NULL,
  `amount_due` decimal(10,2) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `observation` longtext NOT NULL,
  `delivered` tinyint(1) NOT NULL,
  `paid` tinyint(1) NOT NULL,
  `beneficiary_id` char(32) NOT NULL,
  `cause_id` char(32) NOT NULL,
  `checker_id` char(32) NOT NULL,
  `cancellation_reason` longtext,
  `cancelled_at` datetime(6) DEFAULT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `testapp_check_beneficiary_id_b325ed81_fk_testapp_supplier_id` (`beneficiary_id`),
  KEY `testapp_check_cause_id_a20e32eb_fk_testapp_invoice_id` (`cause_id`),
  KEY `testapp_check_checker_id_cbaceab2_fk_testapp_checker_id` (`checker_id`),
  CONSTRAINT `testapp_check_beneficiary_id_b325ed81_fk_testapp_supplier_id` FOREIGN KEY (`beneficiary_id`) REFERENCES `testapp_supplier` (`id`),
  CONSTRAINT `testapp_check_cause_id_a20e32eb_fk_testapp_invoice_id` FOREIGN KEY (`cause_id`) REFERENCES `testapp_invoice` (`id`),
  CONSTRAINT `testapp_check_checker_id_cbaceab2_fk_testapp_checker_id` FOREIGN KEY (`checker_id`) REFERENCES `testapp_checker` (`id`),
  CONSTRAINT `check_amount_cannot_exceed_due` CHECK ((`amount` <= `amount_due`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_check`
--

LOCK TABLES `testapp_check` WRITE;
/*!40000 ALTER TABLE `testapp_check` DISABLE KEYS */;
INSERT INTO `testapp_check` VALUES ('05cc60e5c50444519c991c017b96f3a6','2024-11-23 07:45:45.065353','2024-11-23 09:48:40.243434','THC51360','2024-11-23',NULL,573.00,573.00,'Nothing',1,1,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','bda46172959647eba1a9eaef79e521a2','error','2024-11-23 09:48:40.243379','2024-11-23 10:30:00.000000',NULL,'cancelled'),('089cad86cb4047a7b49bb529324281a4','2024-11-23 11:18:17.863663','2024-11-23 11:18:17.863683','THC51364','2024-11-23',NULL,573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','bda46172959647eba1a9eaef79e521a2',NULL,NULL,NULL,NULL,'pending'),('12f310f9ad1a4bd597e9730da52a49fd','2024-11-23 10:11:27.638993','2024-11-23 10:12:17.581733','THC51363','2024-11-23','2024-12-31',573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','bda46172959647eba1a9eaef79e521a2','RATATOUILLE!!!','2024-11-23 10:12:17.581675',NULL,NULL,'cancelled'),('138dc498966c4560883f3d26072a2780','2024-11-23 11:21:26.368157','2024-11-26 07:54:13.280197','DA990863','2024-11-23',NULL,84.15,84.15,'',0,0,'934792e97d554e708beadf7e1df9deaf','b8ba423caf5d484296a63638b49bb615','70d193f833224198beee5f9388a683b3','shieeet','2024-11-26 07:54:13.279402',NULL,NULL,'cancelled'),('25888525a6574b77917e17c77c81dfb4','2024-11-26 08:20:53.167596','2024-11-26 08:22:46.938898','DAD129501','2024-11-26',NULL,20847.50,16461.90,'',0,0,'934792e97d554e708beadf7e1df9deaf','81934f545c514480be75fa9c4ab6696b','74845e8d56df417b9149bd298bae13c7','Rush','2024-11-26 08:22:46.938108',NULL,NULL,'cancelled'),('259bcd9abc7b410da14678de4b22780d','2024-11-23 10:08:18.350341','2024-11-23 10:17:19.080799','DA990863','2024-11-23',NULL,573.00,573.00,'',1,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','70d193f833224198beee5f9388a683b3','rolf','2024-11-23 10:17:19.080741','2024-11-23 11:17:00.000000',NULL,'cancelled'),('311594473e654e03bc042595fe0faa20','2024-11-23 10:18:21.479292','2024-11-23 10:18:21.479312','DA201201','2024-11-23',NULL,573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','308511a4cf254309bd2466c626afe480',NULL,NULL,NULL,NULL,'pending'),('3cf367b11b8a4773b0ecfdb747b36e9d','2024-11-26 08:24:05.794462','2024-11-26 08:24:05.794488','DAD129502','2024-11-26',NULL,20847.50,8000.00,'Nothin\'',0,0,'934792e97d554e708beadf7e1df9deaf','81934f545c514480be75fa9c4ab6696b','74845e8d56df417b9149bd298bae13c7',NULL,NULL,NULL,NULL,'pending'),('495d4d6737064763a8957fcaa6ddbd89','2024-11-26 15:22:42.188932','2024-11-26 15:22:42.188956','DAD129505','2024-11-26',NULL,11962.36,1000.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','53b6f0cc1e7e4e198e5640607fccca1b','74845e8d56df417b9149bd298bae13c7',NULL,NULL,NULL,NULL,'pending'),('4b62db6fd5364ee1af106be96a702eb8','2024-11-23 11:17:27.821343','2024-11-26 07:54:02.848857','DA201201','2024-11-23',NULL,84.15,84.15,'',0,0,'934792e97d554e708beadf7e1df9deaf','b8ba423caf5d484296a63638b49bb615','308511a4cf254309bd2466c626afe480','Yoooo','2024-11-26 07:54:02.848103',NULL,NULL,'cancelled'),('4b6a96fa8fe84d5fb0390a92d84be972','2024-11-23 10:04:08.434871','2024-11-23 10:05:06.418643','THC51362','2024-11-23',NULL,84.15,84.15,'okay then',1,1,'934792e97d554e708beadf7e1df9deaf','b8ba423caf5d484296a63638b49bb615','bda46172959647eba1a9eaef79e521a2',NULL,NULL,'2024-11-23 11:04:00.000000','2024-11-24 11:04:00.000000','paid'),('54fccea3942c4fa9be8c752434000f0a','2024-11-23 10:57:58.245999','2024-11-26 07:53:32.053890','COC2039656','2024-11-23',NULL,84.15,84.15,'',0,0,'934792e97d554e708beadf7e1df9deaf','b8ba423caf5d484296a63638b49bb615','2c14e26e8fc44580bdcaf5f6f123cc4f','Nothing...','2024-11-26 07:53:32.053064',NULL,NULL,'cancelled'),('7574f65888de43c5a6becfb04a547c32','2024-11-26 15:22:12.505227','2024-11-26 15:23:11.929708','DAD129504','2024-11-26',NULL,11962.36,776.90,'',1,0,'3f1a95ee96f34834ba0b9360e26fc271','53b6f0cc1e7e4e198e5640607fccca1b','74845e8d56df417b9149bd298bae13c7',NULL,NULL,'2024-11-26 16:23:00.000000',NULL,'delivered'),('97816fec54794f079c849a3b81c68d69','2024-11-23 10:19:24.266433','2024-11-23 10:19:24.266452','THC601233','2024-11-23',NULL,573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','417880b442cb4bc5b31b70a16bd673cc',NULL,NULL,NULL,NULL,'pending'),('a175466c66f547038b120340b2731ab1','2024-11-23 10:45:35.068080','2024-11-23 10:45:35.068101','DA990863','2024-11-23',NULL,105.00,105.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','92d8fe4981234bb08ace0e70fb598556','70d193f833224198beee5f9388a683b3',NULL,NULL,NULL,NULL,'pending'),('d2da81e28060430298d2d589b902aeff','2024-11-23 11:23:25.944076','2024-11-23 11:23:25.944102','DAD129500','2024-11-23',NULL,573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','74845e8d56df417b9149bd298bae13c7',NULL,NULL,NULL,NULL,'pending'),('d5884823fb6640d98a9e23b4c4444ebd','2024-11-23 10:56:09.525172','2024-11-23 10:56:09.525193','DA201201','2024-11-23',NULL,573.00,573.00,'',0,0,'3f1a95ee96f34834ba0b9360e26fc271','aeaa13fbc0274ee897d115ac2efc8e0f','308511a4cf254309bd2466c626afe480',NULL,NULL,NULL,NULL,'pending'),('d5c1ee2141f14734bbe80e72cf08c67b','2024-11-23 10:20:54.313872','2024-11-26 07:53:43.947260','COC2039655','2024-11-23',NULL,84.15,84.15,'',0,0,'934792e97d554e708beadf7e1df9deaf','b8ba423caf5d484296a63638b49bb615','2c14e26e8fc44580bdcaf5f6f123cc4f','Bruh..','2024-11-26 07:53:43.946451',NULL,NULL,'cancelled'),('d687ab45dfaf49e081f74103d8c10859','2024-11-23 09:15:55.494312','2024-11-23 09:29:06.555958','THC51361','2024-11-23',NULL,105.00,105.00,'OK2',0,0,'3f1a95ee96f34834ba0b9360e26fc271','92d8fe4981234bb08ace0e70fb598556','bda46172959647eba1a9eaef79e521a2','reason','2024-11-23 09:29:06.555880',NULL,NULL,'cancelled'),('d7cb3918c0af475ea9ce6d8436557ef1','2024-11-26 11:24:46.098674','2024-11-26 11:25:30.388606','DAD129503','2024-11-26',NULL,45787.50,20000.00,'',1,1,'934792e97d554e708beadf7e1df9deaf','69894006045f4f9499a829a3e135887e','74845e8d56df417b9149bd298bae13c7',NULL,NULL,'2024-11-26 12:25:00.000000','2024-11-09 12:25:00.000000','paid');
/*!40000 ALTER TABLE `testapp_check` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_checker`
--

DROP TABLE IF EXISTS `testapp_checker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_checker` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `code` varchar(10) NOT NULL,
  `type` varchar(3) NOT NULL,
  `bank` varchar(4) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `city` varchar(50) NOT NULL,
  `owner` varchar(100) NOT NULL,
  `num_pages` int NOT NULL,
  `index` varchar(3) NOT NULL,
  `starting_page` int NOT NULL,
  `final_page` int NOT NULL,
  `current_position` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_checker`
--

LOCK TABLES `testapp_checker` WRITE;
/*!40000 ALTER TABLE `testapp_checker` DISABLE KEYS */;
INSERT INTO `testapp_checker` VALUES ('2c14e26e8fc44580bdcaf5f6f123cc4f','2024-11-23 10:20:41.710225','2024-11-23 10:57:58.248386','L0OLNIX1','CHQ','BCP','123965','SIDI KACEM','Briqueterie Sidi Kacem',50,'COC',2039655,2039704,2039657),('308511a4cf254309bd2466c626afe480','2024-11-23 10:18:03.193897','2024-11-26 07:54:02.867426','5E1X42J5','CHQ','ATW','1234567890','SIDI KACEM','Briqueterie Sidi Kacem',50,'DA',201201,201250,201202),('417880b442cb4bc5b31b70a16bd673cc','2024-11-23 10:19:02.656071','2024-11-23 10:19:24.268713','CN26YJX5','CHQ','BOA','6009880','SIDI KACEM','Briqueterie Sidi Kacem',50,'THC',601233,601282,601234),('70d193f833224198beee5f9388a683b3','2024-11-23 10:07:32.881020','2024-11-26 07:54:13.298377','PN5DBH2D','LCN','ATW','1234567890','SIDI KACEM','Briqueterie Sidi Kacem',50,'DA',990863,990912,990864),('74845e8d56df417b9149bd298bae13c7','2024-11-23 11:23:14.217049','2024-11-26 15:22:42.206665','SE34PCHG','CHQ','ATW','1234567890','SIDI KACEM','Briqueterie Sidi Kacem',25,'DAD',129500,129524,129506),('bda46172959647eba1a9eaef79e521a2','2024-11-23 07:41:06.027632','2024-11-23 11:18:17.865674','JKC9IB5R','CHQ','BOA','6009880','SIDI KACEM','Briqueterie Sidi Kacem',50,'THC',51360,51409,51365);
/*!40000 ALTER TABLE `testapp_checker` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_exportrecord`
--

DROP TABLE IF EXISTS `testapp_exportrecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_exportrecord` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `exported_at` datetime(6) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `note` longtext NOT NULL,
  `exported_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `testapp_exportrecord_exported_by_id_e7576894_fk_auth_user_id` (`exported_by_id`),
  CONSTRAINT `testapp_exportrecord_exported_by_id_e7576894_fk_auth_user_id` FOREIGN KEY (`exported_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_exportrecord`
--

LOCK TABLES `testapp_exportrecord` WRITE;
/*!40000 ALTER TABLE `testapp_exportrecord` DISABLE KEYS */;
INSERT INTO `testapp_exportrecord` VALUES ('0c9cda652cd84627901d00ee10e061cd','2024-11-23 07:44:32.815000','2024-11-23 07:44:32.815024','2024-11-23 07:44:32.815037','unexport_REF1_20241123_074432','Unexported by codespace',1),('27b8063434b14bf19f6a003e21e92eb3','2024-11-22 14:10:13.151192','2024-11-22 14:10:13.151209','2024-11-22 14:10:13.151217','unexport_REF1_20241122_141013','Unexported by codespace',1),('35c61090bdf8457fa35ca817cabe6876','2024-11-23 07:43:39.415057','2024-11-23 07:43:39.415076','2024-11-23 07:43:39.415083','unexport_REF1_20241123_074339','Unexported by codespace',1),('41c93e30501744e59dedb328d5ac2b9d','2024-11-23 07:44:17.759798','2024-11-23 07:44:17.759818','2024-11-23 07:44:17.759826','accounting_export_20241123_074417.xlsx','',1),('57e118e012e4487c9c76aa040b916d64','2024-11-23 07:44:48.373298','2024-11-23 07:44:48.373316','2024-11-23 07:44:48.373324','unexport_REF1_20241123_074448','Unexported by codespace',1),('61d9b71a94bf46a7bfff1204de67b79a','2024-11-22 14:21:44.006822','2024-11-22 14:21:44.006839','2024-11-22 14:21:44.006847','unexport_REF1_20241122_142144','Unexported by codespace',1),('7359b50fa052430692c23140bf7df99b','2024-11-26 15:51:06.527479','2024-11-26 15:51:06.527498','2024-11-26 15:51:06.527506','accounting_export_20241126_155106.xlsx','',1),('7ad8810bc0144bfd8e50720a6e805f80','2024-11-26 15:51:18.419010','2024-11-26 15:51:18.419029','2024-11-26 15:51:18.419037','unexport_REF2_20241126_155118','Unexported by codespace',1),('853eafee5c8744c483af878f87908125','2024-11-22 14:21:47.430059','2024-11-22 14:21:47.430087','2024-11-22 14:21:47.430100','accounting_export_20241122_142147.xlsx','',1),('858b6cca6590479a8a22634ee9c13e77','2024-11-26 14:47:23.302388','2024-11-26 14:47:23.302408','2024-11-26 14:47:23.302417','accounting_export_20241126_144723.xlsx','',1),('a6fb2de48ead4912af9b87faf8299fea','2024-11-23 07:44:35.800487','2024-11-23 07:44:35.800505','2024-11-23 07:44:35.800513','accounting_export_20241123_074435.xlsx','',1),('adc4635c82b94f5ea6cb4a40f3d52da0','2024-11-22 14:09:27.840129','2024-11-22 14:09:27.840148','2024-11-22 14:09:27.840156','accounting_export_20241122_140927.xlsx','',1),('b2bfbad08ced46bb9b2d134183b2bb8c','2024-11-23 07:44:46.155158','2024-11-23 07:44:46.155175','2024-11-23 07:44:46.155182','unexport_REF2_20241123_074446','Unexported by codespace',1),('baf850beed974bebab89f80e3316a175','2024-11-23 07:44:30.392947','2024-11-23 07:44:30.392966','2024-11-23 07:44:30.392973','unexport_REF2_20241123_074430','Unexported by codespace',1),('c19833416e6b43399f59281196a9013d','2024-11-26 15:51:22.007803','2024-11-26 15:51:22.007822','2024-11-26 15:51:22.007830','accounting_export_20241126_155122.xlsx','',1),('cdac7ede7b9b4a32954d07396cb3023e','2024-11-22 14:10:35.739220','2024-11-22 14:10:35.739238','2024-11-22 14:10:35.739246','accounting_export_20241122_141035.xlsx','',1);
/*!40000 ALTER TABLE `testapp_exportrecord` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_invoice`
--

DROP TABLE IF EXISTS `testapp_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_invoice` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `ref` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `supplier_id` char(32) NOT NULL,
  `payment_due_date` date DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `exported_at` datetime(6) DEFAULT NULL,
  `payment_status` varchar(20) NOT NULL,
  `original_invoice_id` char(32) DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ref` (`ref`),
  UNIQUE KEY `unique_supplier_invoice_ref` (`supplier_id`,`ref`),
  KEY `testapp_invoice_original_invoice_id_0cbf907f_fk_testapp_i` (`original_invoice_id`),
  CONSTRAINT `testapp_invoice_original_invoice_id_0cbf907f_fk_testapp_i` FOREIGN KEY (`original_invoice_id`) REFERENCES `testapp_invoice` (`id`),
  CONSTRAINT `testapp_invoice_supplier_id_6ca11683_fk_testapp_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `testapp_supplier` (`id`),
  CONSTRAINT `credit_note_must_have_original_invoice` CHECK ((((`original_invoice_id` is null) and (`type` = _utf8mb3'invoice')) or ((`original_invoice_id` is not null) and (`type` = _utf8mb3'credit_note'))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_invoice`
--

LOCK TABLES `testapp_invoice` WRITE;
/*!40000 ALTER TABLE `testapp_invoice` DISABLE KEYS */;
INSERT INTO `testapp_invoice` VALUES ('1954b147096d46e6ba3ee0b21357488e','2024-11-26 15:52:32.053832','2024-11-26 15:53:31.126438','REF 9/24','2024-09-09','3f1a95ee96f34834ba0b9360e26fc271','2024-11-08','draft',NULL,'not_paid',NULL,'invoice'),('25fa1517c38949f786c3e449d8ac1a5f','2024-11-26 15:54:46.650036','2024-11-26 15:54:46.650057','CN-REF 9/24','2024-11-26','3f1a95ee96f34834ba0b9360e26fc271',NULL,'draft',NULL,'not_paid','1954b147096d46e6ba3ee0b21357488e','credit_note'),('31c2d204ff50417a8c7781908811672f','2024-11-26 15:20:43.433928','2024-11-26 15:20:43.433948','CN2-REF 7/24','2024-11-26','3f1a95ee96f34834ba0b9360e26fc271',NULL,'draft',NULL,'not_paid','53b6f0cc1e7e4e198e5640607fccca1b','credit_note'),('34e1cba9ac934e11871a8c38bb0c6ffc','2024-11-26 15:55:41.044829','2024-11-26 15:55:41.044863','CN2-REF 9/24','2024-11-26','3f1a95ee96f34834ba0b9360e26fc271',NULL,'draft',NULL,'not_paid','1954b147096d46e6ba3ee0b21357488e','credit_note'),('53b6f0cc1e7e4e198e5640607fccca1b','2024-11-26 15:17:29.390746','2024-11-26 15:23:11.948330','REF 6/24','2024-11-26','3f1a95ee96f34834ba0b9360e26fc271','2025-01-25','draft',NULL,'not_paid',NULL,'invoice'),('69894006045f4f9499a829a3e135887e','2024-11-26 11:22:06.056550','2024-11-26 14:47:23.309443','REF 5/24','2024-05-01','934792e97d554e708beadf7e1df9deaf','2024-06-30','draft','2024-11-26 14:47:23.306051','partially_paid',NULL,'invoice'),('81934f545c514480be75fa9c4ab6696b','2024-11-26 07:59:13.126109','2024-11-26 14:47:23.313403','REF 4/24','2024-02-01','934792e97d554e708beadf7e1df9deaf','2024-04-01','draft','2024-11-26 14:47:23.311880','not_paid',NULL,'invoice'),('92d8fe4981234bb08ace0e70fb598556','2024-11-22 14:57:36.762636','2024-11-26 15:51:22.011912','REF2','2022-02-02','3f1a95ee96f34834ba0b9360e26fc271','2022-04-03','draft','2024-11-26 15:51:22.009763','not_paid',NULL,'invoice'),('aeaa13fbc0274ee897d115ac2efc8e0f','2024-11-22 14:07:40.771275','2024-11-23 07:44:48.375561','REF1','2024-01-01','3f1a95ee96f34834ba0b9360e26fc271','2024-03-01','draft',NULL,'not_paid',NULL,'invoice'),('b8ba423caf5d484296a63638b49bb615','2024-11-23 10:02:31.382515','2024-11-26 07:54:13.296121','REF3/24','2002-01-01','934792e97d554e708beadf7e1df9deaf','2002-03-02','draft',NULL,'paid',NULL,'invoice'),('beb171d2325843649c3396762e1da059','2024-11-26 15:19:55.338180','2024-11-26 15:19:55.338201','CN-REF 7/24','2024-11-26','3f1a95ee96f34834ba0b9360e26fc271',NULL,'draft',NULL,'not_paid','53b6f0cc1e7e4e198e5640607fccca1b','credit_note'),('e6b36445493e48f585214220ad1d975b','2024-11-26 08:07:51.402163','2024-11-26 08:07:51.402185','CN2-REF 4/24','2024-11-26','934792e97d554e708beadf7e1df9deaf',NULL,'draft',NULL,'not_paid','81934f545c514480be75fa9c4ab6696b','credit_note'),('f82bccedaf9b4bfa86aa5d875da58a70','2024-11-26 08:06:19.432031','2024-11-26 08:06:19.432052','CN-REF 4/24','2024-11-26','934792e97d554e708beadf7e1df9deaf',NULL,'draft',NULL,'not_paid','81934f545c514480be75fa9c4ab6696b','credit_note');
/*!40000 ALTER TABLE `testapp_invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_invoice_export_history`
--

DROP TABLE IF EXISTS `testapp_invoice_export_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_invoice_export_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invoice_id` char(32) NOT NULL,
  `exportrecord_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `testapp_invoice_export_h_invoice_id_exportrecord__306d292a_uniq` (`invoice_id`,`exportrecord_id`),
  KEY `testapp_invoice_expo_exportrecord_id_f8da9050_fk_testapp_e` (`exportrecord_id`),
  CONSTRAINT `testapp_invoice_expo_exportrecord_id_f8da9050_fk_testapp_e` FOREIGN KEY (`exportrecord_id`) REFERENCES `testapp_exportrecord` (`id`),
  CONSTRAINT `testapp_invoice_expo_invoice_id_c0a1ae07_fk_testapp_i` FOREIGN KEY (`invoice_id`) REFERENCES `testapp_invoice` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_invoice_export_history`
--

LOCK TABLES `testapp_invoice_export_history` WRITE;
/*!40000 ALTER TABLE `testapp_invoice_export_history` DISABLE KEYS */;
INSERT INTO `testapp_invoice_export_history` VALUES (8,'69894006045f4f9499a829a3e135887e','858b6cca6590479a8a22634ee9c13e77'),(9,'81934f545c514480be75fa9c4ab6696b','858b6cca6590479a8a22634ee9c13e77'),(4,'92d8fe4981234bb08ace0e70fb598556','41c93e30501744e59dedb328d5ac2b9d'),(10,'92d8fe4981234bb08ace0e70fb598556','7359b50fa052430692c23140bf7df99b'),(6,'92d8fe4981234bb08ace0e70fb598556','a6fb2de48ead4912af9b87faf8299fea'),(11,'92d8fe4981234bb08ace0e70fb598556','c19833416e6b43399f59281196a9013d'),(5,'aeaa13fbc0274ee897d115ac2efc8e0f','41c93e30501744e59dedb328d5ac2b9d'),(3,'aeaa13fbc0274ee897d115ac2efc8e0f','853eafee5c8744c483af878f87908125'),(7,'aeaa13fbc0274ee897d115ac2efc8e0f','a6fb2de48ead4912af9b87faf8299fea'),(1,'aeaa13fbc0274ee897d115ac2efc8e0f','adc4635c82b94f5ea6cb4a40f3d52da0'),(2,'aeaa13fbc0274ee897d115ac2efc8e0f','cdac7ede7b9b4a32954d07396cb3023e');
/*!40000 ALTER TABLE `testapp_invoice_export_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_invoiceproduct`
--

DROP TABLE IF EXISTS `testapp_invoiceproduct`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_invoiceproduct` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `reduction_rate` decimal(5,2) NOT NULL,
  `vat_rate` decimal(5,2) NOT NULL,
  `invoice_id` char(32) NOT NULL,
  `product_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `testapp_invoiceproduct_invoice_id_93340a78_fk_testapp_invoice_id` (`invoice_id`),
  KEY `testapp_invoiceproduct_product_id_0e1c77cf_fk_testapp_product_id` (`product_id`),
  CONSTRAINT `testapp_invoiceproduct_invoice_id_93340a78_fk_testapp_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `testapp_invoice` (`id`),
  CONSTRAINT `testapp_invoiceproduct_product_id_0e1c77cf_fk_testapp_product_id` FOREIGN KEY (`product_id`) REFERENCES `testapp_product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_invoiceproduct`
--

LOCK TABLES `testapp_invoiceproduct` WRITE;
/*!40000 ALTER TABLE `testapp_invoiceproduct` DISABLE KEYS */;
INSERT INTO `testapp_invoiceproduct` VALUES ('0292c92664db499aa19665c9c6433f90','2024-11-26 15:19:55.346186','2024-11-26 15:19:55.346215',80,9.85,0.00,20.00,'beb171d2325843649c3396762e1da059','50906b5d19b34b6bacf17fe1504151f2'),('08f63f8ccf2e4b18bbfc1a4c14287c81','2024-11-26 15:20:43.440750','2024-11-26 15:20:43.440765',8,9.85,0.00,20.00,'31c2d204ff50417a8c7781908811672f','50906b5d19b34b6bacf17fe1504151f2'),('0c4408120c214b5bb88f4a3bbc798353','2024-11-26 15:19:25.058300','2024-11-26 15:19:32.913776',777,1.70,0.00,11.00,'53b6f0cc1e7e4e198e5640607fccca1b','ba0f268eb9ad464ba17fe713c52321f1'),('251df0c819db462092de778aa8de107e','2024-11-26 15:54:46.653511','2024-11-26 15:54:46.653533',1994,1.75,2.50,20.00,'25fa1517c38949f786c3e449d8ac1a5f','50906b5d19b34b6bacf17fe1504151f2'),('496810be6f3d4b52a43cfb8b69b66686','2024-11-26 08:03:59.110540','2024-11-26 08:04:27.436448',10,1650.00,5.00,16.00,'81934f545c514480be75fa9c4ab6696b','b7b9beaef4a34fed99bd9b9bd6b0dd5a'),('4b83a8ce89994ffe85d8b0d171c459b4','2024-11-26 15:18:44.339998','2024-11-26 15:19:32.915647',888,9.85,0.00,20.00,'53b6f0cc1e7e4e198e5640607fccca1b','50906b5d19b34b6bacf17fe1504151f2'),('4e7bacf042f146ae82edf17145699d49','2024-11-23 10:03:24.397060','2024-11-23 10:03:24.397078',51,1.50,0.00,10.00,'b8ba423caf5d484296a63638b49bb615','2600a0d03a0d47919493e092ab078c14'),('55e278b8a41e4e7a963933c8f25ddd65','2024-11-22 14:20:13.088647','2024-11-22 14:20:13.088667',10,20.00,10.00,20.00,'aeaa13fbc0274ee897d115ac2efc8e0f','598116423d86499aa10a19946bd94d22'),('5abd1316ba5f4ffeb20e106f7285ca88','2024-11-22 14:08:23.851385','2024-11-22 14:08:23.851406',15,10.00,0.00,10.00,'aeaa13fbc0274ee897d115ac2efc8e0f','2600a0d03a0d47919493e092ab078c14'),('8350338fe38f4225af3b9f0600029dd9','2024-11-26 08:06:19.436469','2024-11-26 08:06:19.436488',25,91.00,0.00,10.00,'f82bccedaf9b4bfa86aa5d875da58a70','25c66d0b4b28490b97b4483615ac1d66'),('84fa6223b6bf4b95b127c869f4cffe22','2024-11-26 08:00:51.009551','2024-11-26 08:04:27.437746',150,0.90,0.00,20.00,'81934f545c514480be75fa9c4ab6696b','598116423d86499aa10a19946bd94d22'),('a1df8d4254a84b7884ffe00ef55f52e0','2024-11-26 08:07:51.405218','2024-11-26 08:07:51.405237',1,1650.00,5.00,16.00,'e6b36445493e48f585214220ad1d975b','b7b9beaef4a34fed99bd9b9bd6b0dd5a'),('a685ef3b99544dc7b0326779b2da558f','2024-11-26 15:20:43.437438','2024-11-26 15:20:43.437462',7,1.70,0.00,11.00,'31c2d204ff50417a8c7781908811672f','ba0f268eb9ad464ba17fe713c52321f1'),('b0c234ce09f2472f8e741f1ab46c1349','2024-11-22 14:21:09.339169','2024-11-22 14:21:09.339192',16,10.00,0.00,20.00,'aeaa13fbc0274ee897d115ac2efc8e0f','99ca80a4c0424f5b8e1e77fba47cbf2a'),('b5cdf0540f9b47459b3e43b449d5a0d8','2024-11-26 08:03:33.702100','2024-11-26 08:04:27.439356',25,91.00,0.00,10.00,'81934f545c514480be75fa9c4ab6696b','25c66d0b4b28490b97b4483615ac1d66'),('c02c0f9fbd60446cac10dcd64d2ce86e','2024-11-23 07:44:06.312975','2024-11-23 07:44:06.312993',35,2.50,0.00,20.00,'92d8fe4981234bb08ace0e70fb598556','99ca80a4c0424f5b8e1e77fba47cbf2a'),('c5bd9a7605574c889d0e2087a4c7cbeb','2024-11-26 15:53:24.863732','2024-11-26 15:53:31.124202',1995,1.75,2.50,20.00,'1954b147096d46e6ba3ee0b21357488e','50906b5d19b34b6bacf17fe1504151f2'),('ca0cccc467be4d449cad7142c69532ec','2024-11-26 08:07:51.408360','2024-11-26 08:07:51.408379',60,0.90,0.00,20.00,'e6b36445493e48f585214220ad1d975b','598116423d86499aa10a19946bd94d22'),('d257d7c11940422c9131e0b57356c608','2024-11-26 11:22:54.747360','2024-11-26 11:23:01.610533',15,2750.00,0.00,11.00,'69894006045f4f9499a829a3e135887e','ba0f268eb9ad464ba17fe713c52321f1'),('e0422f12b8f1400384d7b5a12dce0ef0','2024-11-26 15:55:41.049558','2024-11-26 15:55:41.049585',1,1.75,2.50,20.00,'34e1cba9ac934e11871a8c38bb0c6ffc','50906b5d19b34b6bacf17fe1504151f2'),('edba99bd2438431f982302d5a37cf94e','2024-11-26 15:19:55.342498','2024-11-26 15:19:55.342517',70,1.70,0.00,11.00,'beb171d2325843649c3396762e1da059','ba0f268eb9ad464ba17fe713c52321f1');
/*!40000 ALTER TABLE `testapp_invoiceproduct` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_item`
--

DROP TABLE IF EXISTS `testapp_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_item` (
  `id` char(32) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `quantity` int unsigned NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `testapp_item_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_item`
--

LOCK TABLES `testapp_item` WRITE;
/*!40000 ALTER TABLE `testapp_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `testapp_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_product`
--

DROP TABLE IF EXISTS `testapp_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_product` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `name` varchar(100) NOT NULL,
  `vat_rate` decimal(5,2) NOT NULL,
  `expense_code` varchar(20) NOT NULL,
  `is_energy` tinyint(1) NOT NULL,
  `fiscal_label` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product_name_expense_code` (`name`,`expense_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_product`
--

LOCK TABLES `testapp_product` WRITE;
/*!40000 ALTER TABLE `testapp_product` DISABLE KEYS */;
INSERT INTO `testapp_product` VALUES ('25c66d0b4b28490b97b4483615ac1d66','2024-11-26 08:03:33.621777','2024-11-26 08:03:33.621800','Product6',10.00,'61666',0,'LABEL6'),('2600a0d03a0d47919493e092ab078c14','2024-11-22 14:08:23.764575','2024-11-22 14:08:23.764599','Product3',10.00,'61333',0,'LABEL3'),('50906b5d19b34b6bacf17fe1504151f2','2024-11-26 15:18:44.232954','2024-11-26 15:18:44.232975','Product8',20.00,'61888',0,'LABEL8'),('598116423d86499aa10a19946bd94d22','2024-11-22 14:06:55.697439','2024-11-22 14:06:55.697459','Product1',20.00,'61111',0,'LABEL1'),('99ca80a4c0424f5b8e1e77fba47cbf2a','2024-11-22 14:07:20.280027','2024-11-22 14:07:20.280049','Product2',20.00,'61222',0,'LABEL2'),('ac66c8946d374c7db34cefe842f19bca','2024-11-22 17:08:09.863136','2024-11-22 17:08:09.863161','Product4',20.00,'61444',0,'LABEL4'),('b7b9beaef4a34fed99bd9b9bd6b0dd5a','2024-11-26 08:01:44.516886','2024-11-26 08:01:44.516908','Product5',16.00,'61555',0,'LABEL5'),('ba0f268eb9ad464ba17fe713c52321f1','2024-11-26 11:22:54.670111','2024-11-26 11:22:54.670131','Product7',11.00,'61777',0,'LABEL7');
/*!40000 ALTER TABLE `testapp_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_profile`
--

DROP TABLE IF EXISTS `testapp_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_profile` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `position` varchar(100) NOT NULL,
  `date_of_joining` date DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `contact_number` varchar(15) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `testapp_profile_user_id_0fbb5364_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_profile`
--

LOCK TABLES `testapp_profile` WRITE;
/*!40000 ALTER TABLE `testapp_profile` DISABLE KEYS */;
INSERT INTO `testapp_profile` VALUES ('04092ff0bf2d402ebe11ea4ab79e1788','2024-11-22 14:04:28.102687','2024-11-22 14:05:06.790499','',NULL,NULL,'',2),('ed28974a053840f7a1a3969b7a7093a3','2024-11-22 14:01:25.207145','2024-11-23 07:34:30.153326','',NULL,NULL,'',1);
/*!40000 ALTER TABLE `testapp_profile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_supplier`
--

DROP TABLE IF EXISTS `testapp_supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_supplier` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `name` varchar(100) NOT NULL,
  `if_code` varchar(20) NOT NULL,
  `ice_code` varchar(15) NOT NULL,
  `rc_code` varchar(20) NOT NULL,
  `rc_center` varchar(100) NOT NULL,
  `accounting_code` varchar(20) NOT NULL,
  `is_energy` tinyint(1) NOT NULL,
  `service` varchar(255) NOT NULL,
  `delay_convention` int NOT NULL,
  `is_regulated` tinyint(1) NOT NULL,
  `regulation_file_path` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `if_code` (`if_code`),
  UNIQUE KEY `ice_code` (`ice_code`),
  UNIQUE KEY `accounting_code` (`accounting_code`),
  UNIQUE KEY `testapp_supplier_name_b1d3264a_uniq` (`name`),
  UNIQUE KEY `unique_supplier_name_rc_code` (`name`,`rc_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_supplier`
--

LOCK TABLES `testapp_supplier` WRITE;
/*!40000 ALTER TABLE `testapp_supplier` DISABLE KEYS */;
INSERT INTO `testapp_supplier` VALUES ('3f1a95ee96f34834ba0b9360e26fc271','2024-11-22 14:06:31.607078','2024-11-22 14:06:31.607101','Supplier1','12345','111111111111111','11111','CASAFONIA','44111',0,'CASAPHONISME',60,0,''),('934792e97d554e708beadf7e1df9deaf','2024-11-23 07:42:19.365684','2024-11-23 07:42:19.365713','Supplier2','54321','222222222222222','11111','okbuddy','44222',0,'Motolov',60,0,'');
/*!40000 ALTER TABLE `testapp_supplier` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-11-27  8:16:20
