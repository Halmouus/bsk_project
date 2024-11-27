-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: localhost    Database: django_project
-- ------------------------------------------------------
-- Server version	8.0.36-0ubuntu0.20.04.1

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
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add item',7,'add_item'),(26,'Can change item',7,'change_item'),(27,'Can delete item',7,'delete_item'),(28,'Can view item',7,'view_item'),(29,'Can add profile',8,'add_profile'),(30,'Can change profile',8,'change_profile'),(31,'Can delete profile',8,'delete_profile'),(32,'Can view profile',8,'view_profile'),(33,'Can add product',9,'add_product'),(34,'Can change product',9,'change_product'),(35,'Can delete product',9,'delete_product'),(36,'Can view product',9,'view_product'),(37,'Can add supplier',10,'add_supplier'),(38,'Can change supplier',10,'change_supplier'),(39,'Can delete supplier',10,'delete_supplier'),(40,'Can view supplier',10,'view_supplier'),(41,'Can add invoice',11,'add_invoice'),(42,'Can change invoice',11,'change_invoice'),(43,'Can delete invoice',11,'delete_invoice'),(44,'Can view invoice',11,'view_invoice'),(45,'Can add invoice product',12,'add_invoiceproduct'),(46,'Can change invoice product',12,'change_invoiceproduct'),(47,'Can delete invoice product',12,'delete_invoiceproduct'),(48,'Can view invoice product',12,'view_invoiceproduct'),(49,'Can add export record',13,'add_exportrecord'),(50,'Can change export record',13,'change_exportrecord'),(51,'Can delete export record',13,'delete_exportrecord'),(52,'Can view export record',13,'view_exportrecord'),(53,'Can export invoice',11,'can_export_invoice'),(54,'Can unexport invoice',11,'can_unexport_invoice'),(55,'Can add checker',14,'add_checker'),(56,'Can change checker',14,'change_checker'),(57,'Can delete checker',14,'delete_checker'),(58,'Can view checker',14,'view_checker'),(59,'Can add check',15,'add_check'),(60,'Can change check',15,'change_check'),(61,'Can delete check',15,'delete_check'),(62,'Can view check',15,'view_check');
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$0CIRqmGjkCpUV9fRxyAKcn$duHRuMuqKi//Gch9Hph+TvzSPsY+zMQZHr0hLuNQO/s=','2024-11-18 21:56:28.923688',1,'halmous','','','javierminimaz@gmail.com',1,1,'2024-11-03 17:26:05.140720'),(3,'pbkdf2_sha256$600000$pevL5YjN5EGBUPHKZ2CpqW$PiRYTzSWXNGzBBySWrHKMeMF6Oy7NVG4L1Uimuet+4c=','2024-11-22 18:47:43.605038',0,'admin','Admin','BSK','briqueteriesidikacem@gmail.com',0,1,'2024-11-03 21:50:31.000000'),(4,'pbkdf2_sha256$600000$NxaCpv2vAGdUA7jhOEXGUO$LQyMvSjzvs2rqLCIrWNn6pHsmecoqRV5kssYvin5Qh4=',NULL,0,'user2','','','',0,1,'2024-11-04 21:32:10.074216');
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
INSERT INTO `auth_user_user_permissions` VALUES (1,3,53),(4,3,54);
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
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2024-11-03 17:26:41.449333','654363f8-1ab4-474e-90b3-e406a83255f7','item1',1,'[{\"added\": {}}]',7,1),(2,'2024-11-03 17:27:09.695192','40f1c84d-b58c-4393-8c1b-c8b41659d93f','item2',1,'[{\"added\": {}}]',7,1),(3,'2024-11-03 21:50:31.600217','3','admin',1,'[{\"added\": {}}]',4,1),(4,'2024-11-04 21:32:10.192025','4','user2',1,'[{\"added\": {}}]',4,1),(5,'2024-11-06 16:51:24.818879','3','admin',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Email address\"]}}]',4,1),(6,'2024-11-07 23:13:30.094608','8085978a-6569-4fec-888b-16ae6903f32a','Supplier1',1,'[{\"added\": {}}]',10,1),(7,'2024-11-07 23:16:47.483536','34d8c3f5-9099-48e0-8d44-33ebfe64d51d','Product1',1,'[{\"added\": {}}]',9,1),(8,'2024-11-07 23:17:04.417428','1d2042eb-5644-409a-9944-dedea178b58b','Product2',1,'[{\"added\": {}}]',9,1),(9,'2024-11-07 23:17:17.745901','f77d192a-7277-4efc-a098-5d1c68dc469e','Product3',1,'[{\"added\": {}}]',9,1),(10,'2024-11-07 23:18:48.905526','93958347-7b80-4aba-a802-b226b7dd86ee','Invoice 1646644rf from Supplier1',1,'[{\"added\": {}}]',11,1),(11,'2024-11-07 23:19:11.102897','3f6a893f-9ab8-4442-9cba-f3d214d9c5ac','Product1 on Invoice 1646644rf',1,'[{\"added\": {}}]',12,1),(12,'2024-11-07 23:31:17.163774','064ae3b6-2a42-40ee-b15a-a524e06f54b3','SupplierEn1',1,'[{\"added\": {}}]',10,1),(13,'2024-11-07 23:33:09.130173','38f125d2-efc0-413a-93c9-e9213d7da53d','COOKE',1,'[{\"added\": {}}]',9,1),(14,'2024-11-07 23:35:09.399808','087e885a-7104-4a27-967d-9982386dcbb6','Invoice SJL00000001 from SupplierEn1',1,'[{\"added\": {}}]',11,1),(15,'2024-11-07 23:38:17.362330','f41f0485-1a5c-4ed9-ad73-f1bfccce4147','COOKE on Invoice SJL00000001',1,'[{\"added\": {}}]',12,1),(16,'2024-11-07 23:44:30.712362','f41f0485-1a5c-4ed9-ad73-f1bfccce4147','COOKE on Invoice SJL00000001',3,'',12,1),(17,'2024-11-08 00:32:42.823002','c32f2842-df63-4564-97a2-9444adc17768','HTS',1,'[{\"added\": {}}]',10,1),(18,'2024-11-08 00:33:49.957709','d1f568a8-68e5-4b62-949a-e369db66422c','COKE DE PETRUM',1,'[{\"added\": {}}]',9,1),(19,'2024-11-08 00:34:20.760470','b57b3408-d9cf-46ba-93a7-cac6c5c6190d','Invoice 88556/*DS4 from HTS',1,'[{\"added\": {}}]',11,1),(20,'2024-11-08 00:35:02.386784','4dddd42f-0970-4940-9608-d5d2730fe2e8','COKE DE PETRUM on Invoice 88556/*DS4',1,'[{\"added\": {}}]',12,1);
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
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(15,'testapp','check'),(14,'testapp','checker'),(13,'testapp','exportrecord'),(11,'testapp','invoice'),(12,'testapp','invoiceproduct'),(7,'testapp','item'),(9,'testapp','product'),(8,'testapp','profile'),(10,'testapp','supplier');
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
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-11-03 15:31:46.163525'),(2,'auth','0001_initial','2024-11-03 15:31:47.209525'),(3,'admin','0001_initial','2024-11-03 15:31:47.444246'),(4,'admin','0002_logentry_remove_auto_add','2024-11-03 15:31:47.457937'),(5,'admin','0003_logentry_add_action_flag_choices','2024-11-03 15:31:47.472472'),(6,'contenttypes','0002_remove_content_type_name','2024-11-03 15:31:47.566839'),(7,'auth','0002_alter_permission_name_max_length','2024-11-03 15:31:47.661028'),(8,'auth','0003_alter_user_email_max_length','2024-11-03 15:31:47.689845'),(9,'auth','0004_alter_user_username_opts','2024-11-03 15:31:47.696590'),(10,'auth','0005_alter_user_last_login_null','2024-11-03 15:31:47.762754'),(11,'auth','0006_require_contenttypes_0002','2024-11-03 15:31:47.768637'),(12,'auth','0007_alter_validators_add_error_messages','2024-11-03 15:31:47.779868'),(13,'auth','0008_alter_user_username_max_length','2024-11-03 15:31:48.094213'),(14,'auth','0009_alter_user_last_name_max_length','2024-11-03 15:31:48.187202'),(15,'auth','0010_alter_group_name_max_length','2024-11-03 15:31:48.216579'),(16,'auth','0011_update_proxy_permissions','2024-11-03 15:31:48.228912'),(17,'auth','0012_alter_user_first_name_max_length','2024-11-03 15:31:48.312720'),(18,'sessions','0001_initial','2024-11-03 15:31:48.371932'),(32,'testapp','0001_initial','2024-11-18 15:01:09.564023'),(33,'testapp','0002_item_created_at_item_updated_at_alter_item_id','2024-11-18 15:01:09.705505'),(34,'testapp','0003_profile','2024-11-18 15:02:42.088541'),(35,'testapp','0004_alter_profile_date_of_joining','2024-11-18 15:02:42.162367'),(36,'testapp','0005_invoice_product_supplier_invoiceproduct_and_more','2024-11-18 15:02:42.612168'),(37,'testapp','0006_alter_invoiceproduct_quantity_and_more','2024-11-18 15:02:42.830378'),(38,'testapp','0007_invoice_payment_due_date_invoice_status_and_more','2024-11-18 15:02:42.986495'),(39,'testapp','0008_product_fiscal_label_alter_invoiceproduct_vat_rate_and_more','2024-11-18 15:02:43.056203'),(40,'testapp','0009_remove_invoice_fiscal_label','2024-11-18 21:44:48.090460'),(41,'testapp','0010_invoice_exported_at_exportrecord_and_more','2024-11-20 23:36:59.678364'),(42,'testapp','0011_alter_supplier_name_and_more','2024-11-21 21:10:05.265341'),(43,'testapp','0012_alter_invoice_supplier_alter_invoiceproduct_product','2024-11-21 21:20:41.529198'),(44,'testapp','0013_alter_invoice_options','2024-11-22 18:52:45.422109'),(45,'testapp','0014_checker_check_check_check_amount_cannot_exceed_due','2024-11-22 22:42:34.126965'),(46,'testapp','0015_check_cancellation_reason_check_cancelled_at_and_more','2024-11-23 17:38:13.391865'),(47,'testapp','0016_invoice_payment_status_alter_checker_index','2024-11-24 12:10:26.295135'),(48,'testapp','0017_invoice_original_invoice_invoice_type_and_more','2024-11-24 23:59:27.549641');
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
INSERT INTO `django_session` VALUES ('211h0rjtgz3dnysbi3w9txjrcsvm7pye','.eJxVjEEOwiAQRe_C2hAYChSX7j0DYQZGqoYmpV0Z765NutDtf-_9l4hpW2vcelnilMVZGHH63TDRo7Qd5Htqt1nS3NZlQrkr8qBdXudcnpfD_TuoqddvTZosOKMUBCaFBgNYZZUHbVDn4ClwYgOu5DQEHh1bhoDIQDCMvrB4fwDL8zfU:1tEYgx:Sf-wRbWvjY35Diu7WB3nbYU_fclUGaV-epUXP-qAP2k','2024-12-06 18:47:43.616072'),('k073hsv2kn4rjcdqpqr783vxab2honw5','e30:1t84dE:nAxbEq1qhNrsyHQNcdAYhdmAF5vFX35meTMcL9X_ot0','2024-11-18 21:29:04.591609'),('woo9fge161raspnxi9561i4p5w5o8nvo','e30:1t84YQ:tphg3kir9AnG92HO8HxxhKxKPsUzEpyhISjN4aY5oe0','2024-11-18 21:24:06.545807');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testapp_bankaccount`
--

DROP TABLE IF EXISTS `testapp_bankaccount`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testapp_bankaccount` (
  `id` char(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `bank` varchar(4) NOT NULL,
  `account_number` varchar(30) NOT NULL,
  `accounting_number` varchar(10) NOT NULL,
  `journal_number` varchar(2) NOT NULL,
  `city` varchar(100) NOT NULL,
  `account_type` varchar(15) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_bankaccount`
--

LOCK TABLES `testapp_bankaccount` WRITE;
/*!40000 ALTER TABLE `testapp_bankaccount` DISABLE KEYS */;
/*!40000 ALTER TABLE `testapp_bankaccount` ENABLE KEYS */;
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
  `rejection_date` datetime(6) DEFAULT NULL,
  `rejection_note` longtext NOT NULL DEFAULT (_utf8mb3''),
  `rejection_reason` varchar(50) DEFAULT NULL,
  `replaces_id` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `testapp_check_beneficiary_id_b325ed81_fk_testapp_supplier_id` (`beneficiary_id`),
  KEY `testapp_check_cause_id_a20e32eb_fk_testapp_invoice_id` (`cause_id`),
  KEY `testapp_check_checker_id_cbaceab2_fk_testapp_checker_id` (`checker_id`),
  KEY `testapp_check_replaces_id_2752b866_fk_testapp_check_id` (`replaces_id`),
  CONSTRAINT `testapp_check_beneficiary_id_b325ed81_fk_testapp_supplier_id` FOREIGN KEY (`beneficiary_id`) REFERENCES `testapp_supplier` (`id`),
  CONSTRAINT `testapp_check_cause_id_a20e32eb_fk_testapp_invoice_id` FOREIGN KEY (`cause_id`) REFERENCES `testapp_invoice` (`id`),
  CONSTRAINT `testapp_check_checker_id_cbaceab2_fk_testapp_checker_id` FOREIGN KEY (`checker_id`) REFERENCES `testapp_checker` (`id`),
  CONSTRAINT `testapp_check_replaces_id_2752b866_fk_testapp_check_id` FOREIGN KEY (`replaces_id`) REFERENCES `testapp_check` (`id`),
  CONSTRAINT `check_amount_cannot_exceed_due` CHECK ((`amount` <= `amount_due`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_check`
--

LOCK TABLES `testapp_check` WRITE;
/*!40000 ALTER TABLE `testapp_check` DISABLE KEYS */;
INSERT INTO `testapp_check` VALUES ('07adb945cde646cf9e36025ed6706e4b','2024-11-24 12:31:09.626480','2024-11-24 14:51:18.028906','BI104','2024-11-24',NULL,60.00,60.00,'',1,1,'3f37fde1c63f41bb89bbd49cb48d4a39','5b2d19be3b964520803bcc4fe3c6a033','4844434563554aa49710e67ec8c77a41',NULL,NULL,'2024-11-24 15:50:00.000000','2024-11-24 15:55:00.000000','paid',NULL,'',NULL,NULL),('14c4727f0e46443d8c9e0a4d0f164790','2024-11-24 12:31:15.723201','2024-11-24 13:35:42.280088','BI104','2024-11-24',NULL,60.00,60.00,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','5b2d19be3b964520803bcc4fe3c6a033','4844434563554aa49710e67ec8c77a41','BIG BUUGG','2024-11-24 13:35:42.278562',NULL,NULL,'cancelled',NULL,'',NULL,NULL),('1cc1a1b07dbb4f6ba2aefb592db7a52a','2024-11-23 18:24:24.081536','2024-11-24 19:55:27.554322','BI103','2024-11-23',NULL,28152.84,28152.84,'',1,1,'0df90f27e4e74b2dae3b0c1b36965982','cc2507aa538e4f1dbf43968fe64e4d5d','4844434563554aa49710e67ec8c77a41',NULL,NULL,'2024-11-22 19:25:00.000000','2024-11-24 20:55:00.000000','paid',NULL,'',NULL,NULL),('212c273f612b41b9b6872991b63b7b77','2024-11-25 21:18:44.156527','2024-11-25 21:19:24.711149','BI106','2024-11-25',NULL,192.00,192.00,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','3180420c8b4c4843bf005d86c01b1647','4844434563554aa49710e67ec8c77a41','TEST','2024-11-25 21:19:24.709833',NULL,NULL,'cancelled',NULL,'',NULL,NULL),('35042666f34541fb9c8503243749ca20','2024-11-23 00:44:53.724399','2024-11-23 17:39:28.473938','THC590136','2024-11-23',NULL,342000.00,342000.00,'ok',1,1,'3f37fde1c63f41bb89bbd49cb48d4a39','9f9522a1e100476c95dc415519f2bac4','c25ea15680454ebf828a7465b427ef65','Okay then','2024-11-23 17:39:28.472550',NULL,NULL,'cancelled',NULL,'',NULL,NULL),('5656edae11124068b1d388a901ca222e','2024-11-25 23:58:56.686360','2024-11-25 23:58:56.686391','BI107','2024-11-25',NULL,192.00,153.60,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','3180420c8b4c4843bf005d86c01b1647','4844434563554aa49710e67ec8c77a41',NULL,NULL,NULL,NULL,'pending',NULL,'',NULL,NULL),('7a239600d9ed4509bbea473586bb3b5e','2024-11-24 12:35:11.728526','2024-11-24 13:35:20.764730','BI104','2024-11-24',NULL,60.00,60.00,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','5b2d19be3b964520803bcc4fe3c6a033','4844434563554aa49710e67ec8c77a41','buuug','2024-11-24 13:35:20.763872',NULL,NULL,'cancelled',NULL,'',NULL,NULL),('8264321029104cb598bd83941b68f6d9','2024-11-24 21:13:46.849617','2024-11-24 21:13:46.849635','THC590137','2024-11-24',NULL,7200.00,6000.00,'',0,0,'0df90f27e4e74b2dae3b0c1b36965982','cdd4bd7e5f2b437b8f0a07c31b2673c6','c25ea15680454ebf828a7465b427ef65',NULL,NULL,NULL,NULL,'pending',NULL,'',NULL,NULL),('b6a3a2ea96974207a5684672b7a8f200','2024-11-24 20:13:18.694347','2024-11-25 00:27:40.745214','BI105','2024-11-24',NULL,1225.37,500.00,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','2648bad3322f407882369895d7fa47b8','4844434563554aa49710e67ec8c77a41','TEST','2024-11-25 00:27:40.743699',NULL,NULL,'cancelled',NULL,'',NULL,NULL),('dcffa678c09544b6bc3391ee079d5ccd','2024-11-24 21:33:10.199144','2024-11-24 21:33:10.199181','THC590138','2024-11-24',NULL,7200.00,555.00,'',0,0,'0df90f27e4e74b2dae3b0c1b36965982','cdd4bd7e5f2b437b8f0a07c31b2673c6','c25ea15680454ebf828a7465b427ef65',NULL,NULL,NULL,NULL,'pending',NULL,'',NULL,NULL),('e9b9e6ce43544ee6883715d20432c509','2024-11-23 18:54:12.057805','2024-11-23 18:54:12.057842','BI103','2024-11-23',NULL,342000.00,342000.00,'',0,0,'3f37fde1c63f41bb89bbd49cb48d4a39','9f9522a1e100476c95dc415519f2bac4','4844434563554aa49710e67ec8c77a41',NULL,NULL,NULL,NULL,'pending',NULL,'',NULL,NULL),('fa37ea07a2224132b357a2ec70cdcb1c','2024-11-23 18:44:08.889722','2024-11-24 19:57:17.247956','BI103','2024-11-23',NULL,950.61,950.61,'',1,1,'3f37fde1c63f41bb89bbd49cb48d4a39','2648bad3322f407882369895d7fa47b8','4844434563554aa49710e67ec8c77a41',NULL,NULL,'2024-11-24 12:51:00.000000','2024-11-24 20:57:00.000000','paid',NULL,'',NULL,NULL);
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
  `owner` varchar(100) NOT NULL,
  `num_pages` int NOT NULL,
  `index` varchar(3) NOT NULL,
  `starting_page` int NOT NULL,
  `final_page` int NOT NULL,
  `current_position` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_checker`
--

LOCK TABLES `testapp_checker` WRITE;
/*!40000 ALTER TABLE `testapp_checker` DISABLE KEYS */;
INSERT INTO `testapp_checker` VALUES ('4844434563554aa49710e67ec8c77a41','2024-11-23 18:22:20.219769','2024-11-25 23:58:56.722092','X5W3GOMF','LCN','Briqueterie Sidi Kacem',25,'BI',103,127,108,1),('c25ea15680454ebf828a7465b427ef65','2024-11-23 00:13:15.823392','2024-11-24 21:33:10.227943','IAJTYAKS','CHQ','Briqueterie Sidi Kacem',50,'THC',590136,590185,590139,1);
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
INSERT INTO `testapp_exportrecord` VALUES ('00e8fd5748e0487a8fd504ed3128d132','2024-11-25 21:49:16.041949','2024-11-25 21:49:16.041979','2024-11-25 21:49:16.041991','accounting_export_20241125_214916.xlsx','',3),('0456ed85de8e42f3af5f3fd20fa8247d','2024-11-21 19:11:06.229954','2024-11-21 19:11:06.229985','2024-11-21 19:11:06.229998','unexport_01/24_20241121_191106','Unexported by halmous',1),('0c69ccb8310047bab1d0c15e4c347c56','2024-11-25 21:49:48.735623','2024-11-25 21:49:48.735654','2024-11-25 21:49:48.735666','unexport_REF-EEE-WWW-5/24_20241125_214948','Unexported by admin',3),('112bb1a5ada948f689d59c9810e1c0a0','2024-11-26 23:07:28.171582','2024-11-26 23:07:28.171609','2024-11-26 23:07:28.171618','accounting_export_20241126_230728.xlsx','',3),('12d3fdbeb1444a0fab1a278991cc0543','2024-11-22 21:11:08.844924','2024-11-22 21:11:08.844955','2024-11-22 21:11:08.844967','accounting_export_20241122_211108.xlsx','',3),('137ee2bdda134000bbb7f2f8110378da','2024-11-24 15:30:15.464222','2024-11-24 15:30:15.464250','2024-11-24 15:30:15.464259','accounting_export_20241124_153015.xlsx','',3),('21b1edf3e390491b989b478d51312ea7','2024-11-24 15:29:59.056457','2024-11-24 15:29:59.056489','2024-11-24 15:29:59.056501','unexport_003/2024-O33_20241124_152959','Unexported by admin',3),('2871f0c74b9543509ca161e685c684e8','2024-11-22 19:11:35.736224','2024-11-22 19:11:35.736255','2024-11-22 19:11:35.736268','unexport_01/24_20241122_191135','Unexported by admin',3),('33585b2c5d424c60bb9879bcde47f021','2024-11-21 19:11:12.075873','2024-11-21 19:11:12.075900','2024-11-21 19:11:12.075911','unexport_FA1912_20241121_191112','Unexported by halmous',1),('360518c8e92e4470835d372e11ddb96d','2024-11-24 15:27:23.973582','2024-11-24 15:27:23.973603','2024-11-24 15:27:23.973610','accounting_export_20241124_152723.xlsx','',3),('3a03c2e091534f9ab5688f111debd317','2024-11-21 18:56:08.222090','2024-11-21 18:56:08.222122','2024-11-21 18:56:08.222134','unexport_02/26_20241121_185608','Unexported by halmous',1),('3a954711ffb14bbd84d8860cd8045ad4','2024-11-26 23:48:01.580709','2024-11-26 23:48:01.580741','2024-11-26 23:48:01.580753','unexport_REF-190/24_20241126_234801','Unexported by admin',3),('3d239c5b753b42acb3d399ee3cfa730a','2024-11-22 19:12:28.889710','2024-11-22 19:12:28.889738','2024-11-22 19:12:28.889750','unexport_003/2024_20241122_191228','Unexported by admin',3),('3d70bce3c4494e7e99b602c618c1c350','2024-11-22 19:12:33.084113','2024-11-22 19:12:33.084143','2024-11-22 19:12:33.084157','unexport_EN01/24_20241122_191233','Unexported by admin',3),('3ec2d021bd0f43e99cb0976f0f06bc75','2024-11-22 19:05:29.710119','2024-11-22 19:05:29.710149','2024-11-22 19:05:29.710160','accounting_export_20241122_190529.xlsx','',3),('41909becc1af4a75886b99a94df248e4','2024-11-22 21:12:28.321570','2024-11-22 21:12:28.321593','2024-11-22 21:12:28.321603','accounting_export_20241122_211228.xlsx','',3),('52b7e9a947ce4ac1b44bfef5981ae589','2024-11-21 19:11:14.429275','2024-11-21 19:11:14.429305','2024-11-21 19:11:14.429316','unexport_002/24_20241121_191114','Unexported by halmous',1),('53fc78ac4074470280f3421fd1d3364d','2024-11-21 18:55:36.005595','2024-11-21 18:55:36.005628','2024-11-21 18:55:36.005641','unexport_02/26_20241121_185536','Unexported by halmous',1),('57615c507ea94e7abd23f1a83b3d9ca7','2024-11-23 18:55:33.235762','2024-11-23 18:55:33.235790','2024-11-23 18:55:33.235802','unexport_01/24_20241123_185533','Unexported by admin',3),('59f42fae517749cb94f95d21d0778c81','2024-11-22 21:15:25.386594','2024-11-22 21:15:25.386626','2024-11-22 21:15:25.386640','unexport_01/24_20241122_211525','Unexported by admin',3),('5a3b7860b3b8403f9950e8d2ff91b73f','2024-11-22 20:33:08.297592','2024-11-22 20:33:08.297622','2024-11-22 20:33:08.297633','accounting_export_20241122_203308.xlsx','',3),('5b106139d6f94bcc82c5e8c4ba10f926','2024-11-21 19:11:09.942257','2024-11-21 19:11:09.942290','2024-11-21 19:11:09.942301','unexport_02/26_20241121_191109','Unexported by halmous',1),('5f6df02e700c411d8de3479b870004a6','2024-11-22 20:23:59.866480','2024-11-22 20:23:59.866515','2024-11-22 20:23:59.866527','unexport_01/24_20241122_202359','Unexported by admin',3),('61acd9cc055f4140b8374b5c693f90e5','2024-11-21 18:56:12.892172','2024-11-21 18:56:12.892201','2024-11-21 18:56:12.892213','unexport_002/24_20241121_185612','Unexported by halmous',1),('6dca86ef2c994c0691aca649c7e469ee','2024-11-22 21:11:36.338487','2024-11-22 21:11:36.338517','2024-11-22 21:11:36.338529','unexport_01/24_20241122_211136','Unexported by admin',3),('6fa695d82a9c48d5a426ac337cce01cc','2024-11-22 19:12:27.917312','2024-11-22 19:12:27.917343','2024-11-22 19:12:27.917357','unexport_01/24_20241122_191227','Unexported by admin',3),('7643313f23924dcebb260b8b50bb4975','2024-11-21 18:55:26.122521','2024-11-21 18:55:26.122538','2024-11-21 18:55:26.122546','unexport_FA1912_20241121_185526','Unexported by halmous',1),('7648c997e3ab4ec7b89e0e7ff8eafbed','2024-11-21 19:11:08.093483','2024-11-21 19:11:08.093521','2024-11-21 19:11:08.093534','unexport_003/2024_20241121_191108','Unexported by halmous',1),('77355808ced241c7a234813519888639','2024-11-22 21:10:31.506954','2024-11-22 21:10:31.506984','2024-11-22 21:10:31.506997','unexport_01/24_20241122_211031','Unexported by admin',3),('7a8b0caaa39c44b793244f61cc4b689f','2024-11-22 19:11:46.095936','2024-11-22 19:11:46.095966','2024-11-22 19:11:46.095977','accounting_export_20241122_191146.xlsx','',3),('7ee73861b2184984aca3afa6ffc327b1','2024-11-21 18:55:39.845079','2024-11-21 18:55:39.845114','2024-11-21 18:55:39.845126','unexport_003/2024_20241121_185539','Unexported by halmous',1),('80dd8991e7bf4300bcb10fc3f81fbcc7','2024-11-21 18:56:06.012891','2024-11-21 18:56:06.012923','2024-11-21 18:56:06.012935','unexport_003/2024_20241121_185606','Unexported by halmous',1),('84c871c376cb443797cc73977e126a2c','2024-11-21 18:50:14.735157','2024-11-21 18:50:14.735185','2024-11-21 18:50:14.735196','accounting_export_20241121_185014.xlsx','',1),('871a052decc240ed90eabc0f27e1aec8','2024-11-26 23:41:47.415393','2024-11-26 23:41:47.415428','2024-11-26 23:41:47.415440','unexport_REF-190/24_20241126_234147','Unexported by admin',3),('8d1250defa4c473bbee5761ef2963ee5','2024-11-22 19:12:30.527199','2024-11-22 19:12:30.527228','2024-11-22 19:12:30.527240','unexport_02/26_20241122_191230','Unexported by admin',3),('a07e8be14d52434abdc39b7e7e96e492','2024-11-26 23:41:51.642985','2024-11-26 23:41:51.643016','2024-11-26 23:41:51.643030','accounting_export_20241126_234151.xlsx','',3),('a3615d9433e44cb18dfedf7b376dff4c','2024-11-21 18:56:03.814271','2024-11-21 18:56:03.814301','2024-11-21 18:56:03.814313','unexport_01/24_20241121_185603','Unexported by halmous',1),('a56eb1f0bdae467bab482e818497f1ee','2024-11-23 18:55:11.268641','2024-11-23 18:55:11.268671','2024-11-23 18:55:11.268681','accounting_export_20241123_185511.xlsx','',3),('b5d5f7a021a74796b6b0b9e4935cb8d6','2024-11-22 21:15:29.754807','2024-11-22 21:15:29.754833','2024-11-22 21:15:29.754843','accounting_export_20241122_211529.xlsx','',3),('b878e5e2df7e4630a0dd805f681a3cb0','2024-11-21 18:55:55.084276','2024-11-21 18:55:55.084295','2024-11-21 18:55:55.084302','accounting_export_20241121_185555.xlsx','',1),('bb991ee7104c498d887227760aad7997','2024-11-22 19:12:34.015365','2024-11-22 19:12:34.015395','2024-11-22 19:12:34.015406','unexport_002/24_20241122_191234','Unexported by admin',3),('c5e81dd96502457eac5d13c76dc47d38','2024-11-22 21:15:37.330224','2024-11-22 21:15:37.330257','2024-11-22 21:15:37.330270','unexport_01/24_20241122_211537','Unexported by admin',3),('c86db5e00274497ea19b3ac534ad3de1','2024-11-22 21:10:19.465398','2024-11-22 21:10:19.465422','2024-11-22 21:10:19.465432','accounting_export_20241122_211019.xlsx','',3),('c99f397419c84941aede72795a9fb21a','2024-11-23 23:59:33.347924','2024-11-23 23:59:33.347956','2024-11-23 23:59:33.347968','accounting_export_20241123_235933.xlsx','',3),('cfdfee022b494807b5cc6831b38397c9','2024-11-21 18:31:30.792788','2024-11-21 18:31:30.792812','2024-11-21 18:31:30.792822','accounting_export_20241121_183130.xlsx','',1),('d9c3acb4981b419fb6f3385ba2ad394b','2024-11-21 18:56:10.500027','2024-11-21 18:56:10.500056','2024-11-21 18:56:10.500067','unexport_FA1912_20241121_185610','Unexported by halmous',1),('de9a5bd7466948bfa5b0f95893026b4d','2024-11-21 18:55:42.326958','2024-11-21 18:55:42.326986','2024-11-21 18:55:42.326997','unexport_01/24_20241121_185542','Unexported by halmous',1),('f227e478a2684c66a67a311b23b68ec6','2024-11-21 18:56:19.460230','2024-11-21 18:56:19.460253','2024-11-21 18:56:19.460261','accounting_export_20241121_185619.xlsx','',1),('f9521ab7cde941148498a1152a9f69d6','2024-11-22 20:33:11.905499','2024-11-22 20:33:11.905529','2024-11-22 20:33:11.905541','unexport_01/24_20241122_203311','Unexported by admin',3),('fe26986936de4bd4848ae270fc860e72','2024-11-22 19:51:55.195775','2024-11-22 19:51:55.195806','2024-11-22 19:51:55.195818','accounting_export_20241122_195155.xlsx','',3),('fe54df9224e34b69ba33f7f6523b137f','2024-11-22 19:12:31.621945','2024-11-22 19:12:31.621977','2024-11-22 19:12:31.621990','unexport_FA1912_20241122_191231','Unexported by admin',3);
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
INSERT INTO `testapp_invoice` VALUES ('2648bad3322f407882369895d7fa47b8','2024-11-18 20:45:06.702788','2024-11-25 00:27:40.777374','01/24-O1','2024-01-31','3f37fde1c63f41bb89bbd49cb48d4a39','2024-03-01','draft','2024-11-23 23:59:33.358199','partially_paid',NULL,'invoice'),('3180420c8b4c4843bf005d86c01b1647','2024-11-25 19:43:54.986466','2024-11-26 23:07:28.194647','REF-EEE-WWW-5/60','2020-05-05','3f37fde1c63f41bb89bbd49cb48d4a39','2020-07-04','draft','2024-11-26 23:07:28.184492','not_paid',NULL,'invoice'),('35a1191620ec4101807799029e836edd','2024-11-25 21:16:17.304447','2024-11-25 21:16:17.304473','CN-REF-01/25','2024-11-25','3f37fde1c63f41bb89bbd49cb48d4a39',NULL,'draft',NULL,'not_paid','3180420c8b4c4843bf005d86c01b1647','credit_note'),('4f44e297d4044e9eadc0d60669c85f8e','2024-11-25 20:18:42.920093','2024-11-25 20:18:42.920126','CN-REF-EEE-WWW-5/24','2024-11-25','3f37fde1c63f41bb89bbd49cb48d4a39','2025-01-24','draft',NULL,'not_paid','3180420c8b4c4843bf005d86c01b1647','credit_note'),('56ff94b5d45b48bf93a5a411847e32ca','2024-11-19 22:49:22.570506','2024-11-24 15:30:15.482589','003/2024-O33','2024-01-31','3f37fde1c63f41bb89bbd49cb48d4a39','2024-03-01','draft','2024-11-24 15:30:15.473853','not_paid',NULL,'invoice'),('5b2d19be3b964520803bcc4fe3c6a033','2024-11-19 22:14:33.146948','2024-11-24 14:51:18.053720','02/26','2026-01-01','3f37fde1c63f41bb89bbd49cb48d4a39','2026-03-02','draft',NULL,'paid',NULL,'invoice'),('62f4f1e6b3a74a47bd4ede2f46935c17','2024-11-24 11:20:11.007472','2024-11-24 15:30:15.496279','004/24-5','2024-06-30','3f37fde1c63f41bb89bbd49cb48d4a39','2024-08-29','draft','2024-11-24 15:30:15.488693','not_paid',NULL,'invoice'),('9f9522a1e100476c95dc415519f2bac4','2024-11-20 20:46:55.131339','2024-11-26 23:07:28.210301','FA1912','2024-11-20','3f37fde1c63f41bb89bbd49cb48d4a39','2025-01-19','draft','2024-11-26 23:07:28.203021','not_paid',NULL,'invoice'),('cc2507aa538e4f1dbf43968fe64e4d5d','2024-11-22 00:15:06.904040','2024-11-26 23:07:28.226107','EN01/24','2019-01-01','0df90f27e4e74b2dae3b0c1b36965982','2019-03-02','draft','2024-11-26 23:07:28.218183','partially_paid',NULL,'invoice'),('cdd4bd7e5f2b437b8f0a07c31b2673c6','2024-11-24 01:01:03.084505','2024-11-26 23:48:01.591739','REF-190/24','2024-12-31','0df90f27e4e74b2dae3b0c1b36965982','2025-03-01','draft',NULL,'not_paid',NULL,'invoice');
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
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_invoice_export_history`
--

LOCK TABLES `testapp_invoice_export_history` WRITE;
/*!40000 ALTER TABLE `testapp_invoice_export_history` DISABLE KEYS */;
INSERT INTO `testapp_invoice_export_history` VALUES (25,'2648bad3322f407882369895d7fa47b8','12d3fdbeb1444a0fab1a278991cc0543'),(15,'2648bad3322f407882369895d7fa47b8','3ec2d021bd0f43e99cb0976f0f06bc75'),(26,'2648bad3322f407882369895d7fa47b8','41909becc1af4a75886b99a94df248e4'),(23,'2648bad3322f407882369895d7fa47b8','5a3b7860b3b8403f9950e8d2ff91b73f'),(16,'2648bad3322f407882369895d7fa47b8','7a8b0caaa39c44b793244f61cc4b689f'),(28,'2648bad3322f407882369895d7fa47b8','a56eb1f0bdae467bab482e818497f1ee'),(27,'2648bad3322f407882369895d7fa47b8','b5d5f7a021a74796b6b0b9e4935cb8d6'),(5,'2648bad3322f407882369895d7fa47b8','b878e5e2df7e4630a0dd805f681a3cb0'),(24,'2648bad3322f407882369895d7fa47b8','c86db5e00274497ea19b3ac534ad3de1'),(29,'2648bad3322f407882369895d7fa47b8','c99f397419c84941aede72795a9fb21a'),(1,'2648bad3322f407882369895d7fa47b8','cfdfee022b494807b5cc6831b38397c9'),(10,'2648bad3322f407882369895d7fa47b8','f227e478a2684c66a67a311b23b68ec6'),(22,'2648bad3322f407882369895d7fa47b8','fe26986936de4bd4848ae270fc860e72'),(33,'3180420c8b4c4843bf005d86c01b1647','00e8fd5748e0487a8fd504ed3128d132'),(34,'3180420c8b4c4843bf005d86c01b1647','112bb1a5ada948f689d59c9810e1c0a0'),(31,'56ff94b5d45b48bf93a5a411847e32ca','137ee2bdda134000bbb7f2f8110378da'),(30,'56ff94b5d45b48bf93a5a411847e32ca','360518c8e92e4470835d372e11ddb96d'),(17,'56ff94b5d45b48bf93a5a411847e32ca','7a8b0caaa39c44b793244f61cc4b689f'),(2,'56ff94b5d45b48bf93a5a411847e32ca','84c871c376cb443797cc73977e126a2c'),(6,'56ff94b5d45b48bf93a5a411847e32ca','b878e5e2df7e4630a0dd805f681a3cb0'),(11,'56ff94b5d45b48bf93a5a411847e32ca','f227e478a2684c66a67a311b23b68ec6'),(18,'5b2d19be3b964520803bcc4fe3c6a033','7a8b0caaa39c44b793244f61cc4b689f'),(3,'5b2d19be3b964520803bcc4fe3c6a033','84c871c376cb443797cc73977e126a2c'),(7,'5b2d19be3b964520803bcc4fe3c6a033','b878e5e2df7e4630a0dd805f681a3cb0'),(12,'5b2d19be3b964520803bcc4fe3c6a033','f227e478a2684c66a67a311b23b68ec6'),(32,'62f4f1e6b3a74a47bd4ede2f46935c17','137ee2bdda134000bbb7f2f8110378da'),(35,'9f9522a1e100476c95dc415519f2bac4','112bb1a5ada948f689d59c9810e1c0a0'),(19,'9f9522a1e100476c95dc415519f2bac4','7a8b0caaa39c44b793244f61cc4b689f'),(4,'9f9522a1e100476c95dc415519f2bac4','84c871c376cb443797cc73977e126a2c'),(8,'9f9522a1e100476c95dc415519f2bac4','b878e5e2df7e4630a0dd805f681a3cb0'),(13,'9f9522a1e100476c95dc415519f2bac4','f227e478a2684c66a67a311b23b68ec6'),(36,'cc2507aa538e4f1dbf43968fe64e4d5d','112bb1a5ada948f689d59c9810e1c0a0'),(20,'cc2507aa538e4f1dbf43968fe64e4d5d','7a8b0caaa39c44b793244f61cc4b689f'),(37,'cdd4bd7e5f2b437b8f0a07c31b2673c6','112bb1a5ada948f689d59c9810e1c0a0'),(38,'cdd4bd7e5f2b437b8f0a07c31b2673c6','a07e8be14d52434abdc39b7e7e96e492');
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
INSERT INTO `testapp_invoiceproduct` VALUES ('13d73721f1f44a16975bec8e0cdb47f1','2024-11-20 20:47:37.432070','2024-11-20 22:46:45.304949',150,2000.00,5.00,20.00,'9f9522a1e100476c95dc415519f2bac4','fb5ab7197b59404bbff41f39a5ee1416'),('27d1fc34e5944dff9f87fd2288f413ce','2024-11-25 21:16:17.318326','2024-11-25 21:16:17.318359',1,16.00,0.00,20.00,'35a1191620ec4101807799029e836edd','31bb62977e8e48f48b56d4024b9eab54'),('299c23f7f6004cb6be9e0adcd7260713','2024-11-25 19:44:35.366166','2024-11-25 22:15:19.228894',10,16.00,0.00,20.00,'3180420c8b4c4843bf005d86c01b1647','31bb62977e8e48f48b56d4024b9eab54'),('317f7210163d46e283dae54c1821704e','2024-11-19 23:17:15.429428','2024-11-24 11:19:38.701183',200,16.07,5.00,7.00,'56ff94b5d45b48bf93a5a411847e32ca','bf8d73d65bdc4271806c7652166a9fe0'),('5290be2da8b941e8afa3c049c6dca05b','2024-11-22 00:19:42.154183','2024-11-22 00:19:42.154215',20,1200.00,0.00,10.00,'cc2507aa538e4f1dbf43968fe64e4d5d','e85c8388ab5a4c93bde40e675c3aa363'),('60938d1f72bd4c59bd8af57a3adbec3c','2024-11-22 20:58:58.428364','2024-11-23 23:58:40.515174',25,26.00,0.99,11.00,'2648bad3322f407882369895d7fa47b8','fb5ab7197b59404bbff41f39a5ee1416'),('86d38bb35b6b46b4ba9ab7437298d4ba','2024-11-25 20:18:42.938149','2024-11-25 20:18:42.938182',1,16.00,0.00,20.00,'4f44e297d4044e9eadc0d60669c85f8e','31bb62977e8e48f48b56d4024b9eab54'),('9c9ff0027c91453da2a5a3a9e2cc9945','2024-11-22 19:13:29.976435','2024-11-22 19:13:29.976468',56,19.00,1.50,10.00,'cc2507aa538e4f1dbf43968fe64e4d5d','a4522c8fa81942d789b4b4249f6693bc'),('9efab82b6aff46fd95f3af522c0babc1','2024-11-19 23:25:44.221472','2024-11-24 01:48:23.301735',2,20.00,0.00,0.00,'56ff94b5d45b48bf93a5a411847e32ca','fb5ab7197b59404bbff41f39a5ee1416'),('ab17abae060b463689a495164462b817','2024-11-18 20:47:30.761012','2024-11-19 21:58:22.505410',10,6.00,0.00,20.00,'2648bad3322f407882369895d7fa47b8','fb5ab7197b59404bbff41f39a5ee1416'),('b2cdfd1514de482c84c4120bb5293a88','2024-11-18 20:46:29.280571','2024-11-20 21:41:01.127141',12,10.00,0.00,20.00,'2648bad3322f407882369895d7fa47b8','fb5ab7197b59404bbff41f39a5ee1416'),('b7f05f64e0094bc5902c8e0422be4999','2024-11-24 11:27:37.750162','2024-11-24 11:27:46.695877',26,6.00,0.50,20.00,'62f4f1e6b3a74a47bd4ede2f46935c17','441c691c0c004b06bceaf023873796d6'),('ba415fdd52f649c590a0c018e724da75','2024-11-22 18:44:32.744660','2024-11-22 18:45:21.343267',15,23.50,50.00,10.00,'2648bad3322f407882369895d7fa47b8','441c691c0c004b06bceaf023873796d6'),('c4d1529dcd7244eaa22f7121dff3c9f0','2024-11-22 19:19:02.625485','2024-11-22 19:19:02.625511',50,10.00,0.00,20.00,'cc2507aa538e4f1dbf43968fe64e4d5d','096307b176d74494b34c6407b86876cb'),('d8d5f53a63e64bc4bbef0b4aeae34c1a','2024-11-21 21:19:02.989711','2024-11-21 21:22:50.487582',5,18.50,1.50,11.00,'2648bad3322f407882369895d7fa47b8','09762195a2924845b32a182682520e96'),('da08a2f83ff149acaa31e45e5b2003ae','2024-11-24 01:01:25.084746','2024-11-24 01:01:31.219477',50,120.00,0.00,20.00,'cdd4bd7e5f2b437b8f0a07c31b2673c6','096307b176d74494b34c6407b86876cb'),('fb50cc3723394fa68aa91000ac4cdb4d','2024-11-19 23:16:45.133276','2024-11-19 23:16:45.133304',5,10.00,0.00,20.00,'5b2d19be3b964520803bcc4fe3c6a033','fb5ab7197b59404bbff41f39a5ee1416');
/*!40000 ALTER TABLE `testapp_invoiceproduct` ENABLE KEYS */;
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
INSERT INTO `testapp_product` VALUES ('096307b176d74494b34c6407b86876cb','2024-11-22 19:19:02.601743','2024-11-24 10:47:33.292720','Energy404',20.00,'6122104',1,'ENERGY404'),('09762195a2924845b32a182682520e96','2024-11-21 21:10:54.449789','2024-11-21 21:10:54.449829','Product3',20.00,'613332',0,'Label3'),('31bb62977e8e48f48b56d4024b9eab54','2024-11-22 20:06:23.233144','2024-11-22 20:06:23.233179','Product6',20.00,'61555',0,'LABEL6'),('441c691c0c004b06bceaf023873796d6','2024-11-21 19:21:39.921037','2024-11-21 19:27:11.390577','Product4',20.00,'61444',0,'Label5'),('6b9d96061da241129f15dabc87e9fa09','2024-11-20 20:46:00.457883','2024-11-22 20:16:40.771525','Product3',7.00,'61333',0,'Label3'),('a4522c8fa81942d789b4b4249f6693bc','2024-11-21 22:32:19.626481','2024-11-22 19:58:08.894155','Energy2',10.00,'6122102',1,'ENERGY2'),('b89aa716de3d41bdbcc445dd4b12cae4','2024-11-22 19:14:25.249220','2024-11-22 19:14:25.249253','Energy3',20.00,'6122103',1,'ENERGY3'),('bf8d73d65bdc4271806c7652166a9fe0','2024-11-18 20:46:12.135800','2024-11-22 19:57:40.169976','Product2',7.00,'61222',0,'FISLAB2'),('e85c8388ab5a4c93bde40e675c3aa363','2024-11-21 22:31:40.994244','2024-11-21 22:31:40.994280','Energy1',10.00,'6122101',1,'ENERGY1'),('fb5ab7197b59404bbff41f39a5ee1416','2024-11-18 20:45:53.970454','2024-11-22 19:57:46.224075','Product1',11.00,'61111',0,'FISLAB1');
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
INSERT INTO `testapp_supplier` VALUES ('0df90f27e4e74b2dae3b0c1b36965982','2024-11-22 00:14:16.041733','2024-11-22 00:14:32.506981','EnergySupplier1','99999','999999999999999','99999','SAN ANDREAS','44999',1,'BIG ENERGY',60,0,''),('3f37fde1c63f41bb89bbd49cb48d4a39','2024-11-18 20:44:07.975385','2024-11-22 19:49:11.131099','Supplier1','12345','121212121212121','12317','KAKIN CITY','4411281',0,'KAKINOO',60,0,'');
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

-- Dump completed on 2024-11-27  2:32:06
