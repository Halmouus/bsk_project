# backup.sql

```sql
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
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add item',7,'add_item'),(26,'Can change item',7,'change_item'),(27,'Can delete item',7,'delete_item'),(28,'Can view item',7,'view_item'),(29,'Can add profile',8,'add_profile'),(30,'Can change profile',8,'change_profile'),(31,'Can delete profile',8,'delete_profile'),(32,'Can view profile',8,'view_profile'),(33,'Can add product',9,'add_product'),(34,'Can change product',9,'change_product'),(35,'Can delete product',9,'delete_product'),(36,'Can view product',9,'view_product'),(37,'Can add supplier',10,'add_supplier'),(38,'Can change supplier',10,'change_supplier'),(39,'Can delete supplier',10,'delete_supplier'),(40,'Can view supplier',10,'view_supplier'),(41,'Can add invoice',11,'add_invoice'),(42,'Can change invoice',11,'change_invoice'),(43,'Can delete invoice',11,'delete_invoice'),(44,'Can view invoice',11,'view_invoice'),(45,'Can add invoice product',12,'add_invoiceproduct'),(46,'Can change invoice product',12,'change_invoiceproduct'),(47,'Can delete invoice product',12,'delete_invoiceproduct'),(48,'Can view invoice product',12,'view_invoiceproduct');
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
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$0CIRqmGjkCpUV9fRxyAKcn$duHRuMuqKi//Gch9Hph+TvzSPsY+zMQZHr0hLuNQO/s=','2024-11-18 01:41:04.619351',1,'halmous','','','javierminimaz@gmail.com',1,1,'2024-11-03 17:26:05.140720'),(3,'pbkdf2_sha256$600000$pevL5YjN5EGBUPHKZ2CpqW$PiRYTzSWXNGzBBySWrHKMeMF6Oy7NVG4L1Uimuet+4c=','2024-11-18 02:11:44.729093',0,'admin','Admin','BSK','briqueteriesidikacem@gmail.com',0,1,'2024-11-03 21:50:31.000000'),(4,'pbkdf2_sha256$600000$NxaCpv2vAGdUA7jhOEXGUO$LQyMvSjzvs2rqLCIrWNn6pHsmecoqRV5kssYvin5Qh4=',NULL,0,'user2','','','',0,1,'2024-11-04 21:32:10.074216');
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
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(11,'testapp','invoice'),(12,'testapp','invoiceproduct'),(7,'testapp','item'),(9,'testapp','product'),(8,'testapp','profile'),(10,'testapp','supplier');
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
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-11-03 15:31:46.163525'),(2,'auth','0001_initial','2024-11-03 15:31:47.209525'),(3,'admin','0001_initial','2024-11-03 15:31:47.444246'),(4,'admin','0002_logentry_remove_auto_add','2024-11-03 15:31:47.457937'),(5,'admin','0003_logentry_add_action_flag_choices','2024-11-03 15:31:47.472472'),(6,'contenttypes','0002_remove_content_type_name','2024-11-03 15:31:47.566839'),(7,'auth','0002_alter_permission_name_max_length','2024-11-03 15:31:47.661028'),(8,'auth','0003_alter_user_email_max_length','2024-11-03 15:31:47.689845'),(9,'auth','0004_alter_user_username_opts','2024-11-03 15:31:47.696590'),(10,'auth','0005_alter_user_last_login_null','2024-11-03 15:31:47.762754'),(11,'auth','0006_require_contenttypes_0002','2024-11-03 15:31:47.768637'),(12,'auth','0007_alter_validators_add_error_messages','2024-11-03 15:31:47.779868'),(13,'auth','0008_alter_user_username_max_length','2024-11-03 15:31:48.094213'),(14,'auth','0009_alter_user_last_name_max_length','2024-11-03 15:31:48.187202'),(15,'auth','0010_alter_group_name_max_length','2024-11-03 15:31:48.216579'),(16,'auth','0011_update_proxy_permissions','2024-11-03 15:31:48.228912'),(17,'auth','0012_alter_user_first_name_max_length','2024-11-03 15:31:48.312720'),(18,'sessions','0001_initial','2024-11-03 15:31:48.371932');
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
INSERT INTO `django_session` VALUES ('bqedjk6svyl87ok5shhj2uzqs9jthm60','.eJxVjEEOwiAQRe_C2hAYChSX7j0DYQZGqoYmpV0Z765NutDtf-_9l4hpW2vcelnilMVZGHH63TDRo7Qd5Htqt1nS3NZlQrkr8qBdXudcnpfD_TuoqddvTZosOKMUBCaFBgNYZZUHbVDn4ClwYgOu5DQEHh1bhoDIQDCMvrB4fwDL8zfU:1tCrEu:BZhdtPPgTz4z37gVTp5Gx_d6oQPnuE-UuPEYIq3fZ_E','2024-12-02 02:11:44.749281'),('k073hsv2kn4rjcdqpqr783vxab2honw5','e30:1t84dE:nAxbEq1qhNrsyHQNcdAYhdmAF5vFX35meTMcL9X_ot0','2024-11-18 21:29:04.591609'),('woo9fge161raspnxi9561i4p5w5o8nvo','e30:1t84YQ:tphg3kir9AnG92HO8HxxhKxKPsUzEpyhISjN4aY5oe0','2024-11-18 21:24:06.545807');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
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
  `fiscal_label` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ref` (`ref`),
  KEY `testapp_invoice_supplier_id_6ca11683_fk_testapp_supplier_id` (`supplier_id`),
  CONSTRAINT `testapp_invoice_supplier_id_6ca11683_fk_testapp_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `testapp_supplier` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_invoice`
--

LOCK TABLES `testapp_invoice` WRITE;
/*!40000 ALTER TABLE `testapp_invoice` DISABLE KEYS */;
INSERT INTO `testapp_invoice` VALUES ('28e9496850564cd48d77c2bc5f869418','2024-11-18 12:58:30.682203','2024-11-18 12:59:29.046407','02/25','2024-02-01','c32f2842df63456497a29444adc17768','2024-05-01','draft','brocoli'),('33abe58a252c49949d6ee45f386caf66','2024-11-15 20:41:11.623411','2024-11-15 21:01:45.207313','001/24','2024-11-15','c32f2842df63456497a29444adc17768',NULL,'draft',''),('35dd4474e01d4b048e13a971ddde2b32','2024-11-17 11:58:58.577056','2024-11-17 11:58:58.593587','10/024','2024-01-01','c32f2842df63456497a29444adc17768',NULL,'draft',''),('46a62459c76040a5996feec85522f833','2024-11-18 00:13:48.743892','2024-11-18 00:13:48.757282','test1','2005-02-01','c32f2842df63456497a29444adc17768',NULL,'draft',''),('57853b4952524d06b4343f7a44ab9800','2024-11-15 22:01:08.999521','2024-11-15 22:01:09.018041','03/2024','2024-11-08','c32f2842df63456497a29444adc17768',NULL,'draft',''),('b8bd94003c9945648028d5720a7c601f','2024-11-17 17:54:57.685891','2024-11-17 17:54:57.701224','shhhh','2050-05-01','c32f2842df63456497a29444adc17768',NULL,'draft',''),('c5e8719da9a140208eb901768f96f5a1','2024-11-17 23:46:18.800309','2024-11-17 23:47:54.106780','abcd012','2003-02-01','c32f2842df63456497a29444adc17768',NULL,'draft',''),('d15021e6ee1942c8a92850f177ec72b8','2024-11-17 12:07:57.562049','2024-11-17 12:07:57.577636','F/24/150/12.14','2024-07-22','46d97fc9f81c420588a8a5e96ca0d375',NULL,'draft','');
/*!40000 ALTER TABLE `testapp_invoice` ENABLE KEYS */;
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
INSERT INTO `testapp_invoiceproduct` VALUES ('2e9d4dffe5384e329635e2306756bcfe','2024-11-17 17:54:57.693445','2024-11-17 17:54:57.693474',1,100.00,0.00,20.00,'b8bd94003c9945648028d5720a7c601f','1d2042eb5644409a9944dedea178b58b'),('48cc1f5761534004bb9646b094827f2d','2024-11-15 22:01:09.008961','2024-11-15 22:01:09.009005',1,100.00,0.00,20.00,'57853b4952524d06b4343f7a44ab9800','d1f568a868e54b62949ae369db66422c'),('58b0df56c9924361a95d4fdc65a7e328','2024-11-17 12:07:57.568384','2024-11-17 12:07:57.568405',1,2000.00,0.00,20.00,'d15021e6ee1942c8a92850f177ec72b8','f1838c82eed54eb1b5c72ce8f363718b'),('752474463abc404ab9428fa40ec9c23b','2024-11-18 00:13:48.751468','2024-11-18 00:13:48.751498',55,100.00,0.00,20.00,'46a62459c76040a5996feec85522f833','38f125d2efc0413a93c9e9213d7da53d'),('875c9598042c4b259004fce265e445ec','2024-11-17 11:58:58.583909','2024-11-17 11:58:58.583934',5,20.00,0.00,20.00,'35dd4474e01d4b048e13a971ddde2b32','d1f568a868e54b62949ae369db66422c'),('9d60a2c74f664a42bd7be9586dd6caef','2024-11-17 23:46:47.981616','2024-11-17 23:47:54.098294',10,25.00,0.00,20.00,'c5e8719da9a140208eb901768f96f5a1','34d8c3f5909948e08d4433ebfe64d51d'),('b584cb77dcbb41f78bbb7505c5873012','2024-11-17 11:58:58.588078','2024-11-17 11:58:58.588099',10,5.00,0.00,10.00,'35dd4474e01d4b048e13a971ddde2b32','38f125d2efc0413a93c9e9213d7da53d'),('d67aea0f49fb4fc8a0f9670616562def','2024-11-17 23:46:18.807577','2024-11-17 23:47:54.103159',1000,5.00,1.00,14.00,'c5e8719da9a140208eb901768f96f5a1','1d2042eb5644409a9944dedea178b58b'),('df960dde9fc94305bf842123c67ed84a','2024-11-15 20:41:11.632330','2024-11-15 20:44:03.112128',1,10.00,5.00,20.00,'33abe58a252c49949d6ee45f386caf66','38f125d2efc0413a93c9e9213d7da53d'),('e42d6e59c3744aee93d6b313ca24e8ee','2024-11-15 20:45:19.803355','2024-11-15 21:01:45.197544',1,10.00,90.00,10.00,'33abe58a252c49949d6ee45f386caf66','38f125d2efc0413a93c9e9213d7da53d'),('ed041d42ce0845118388cf449805f697','2024-11-17 12:07:57.573532','2024-11-17 12:07:57.573553',1,500.00,0.00,20.00,'d15021e6ee1942c8a92850f177ec72b8','ded98978892c4942ba1e0a162af4cbc8');
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
INSERT INTO `testapp_item` VALUES ('40f1c84db58c43938c1bc8b41659d93f','item2','desc2',5,29.99,'2024-11-03 17:27:09.694384','2024-11-03 17:27:09.694414'),('654363f81ab4474e90b3e406a83255f7','item1','desc1',1,15.35,'2024-11-03 17:26:41.447943','2024-11-03 17:26:41.447994');
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
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_product`
--

LOCK TABLES `testapp_product` WRITE;
/*!40000 ALTER TABLE `testapp_product` DISABLE KEYS */;
INSERT INTO `testapp_product` VALUES ('1d2042eb5644409a9944dedea178b58b','2024-11-07 23:17:04.415940','2024-11-07 23:17:04.415989','Product2',14.00,'61223',0,'TESTLABEL'),('34d8c3f5909948e08d4433ebfe64d51d','2024-11-07 23:16:47.482496','2024-11-07 23:16:47.482528','Product1',20.00,'61225',0,'TESTLABEL'),('38f125d2efc0413a93c9e9213d7da53d','2024-11-07 23:33:09.129126','2024-11-07 23:33:09.129161','COOKE',35.00,'61221',1,'TESTLABEL'),('8f03e80c7d3d49219f03e2a3b9b0f7e4','2024-11-17 13:20:49.345969','2024-11-17 13:21:15.025358','ProductX',0.00,'611995',0,'TESTLABEL'),('d1f568a868e54b62949ae369db66422c','2024-11-08 00:33:49.956802','2024-11-08 00:33:49.956836','COKE DE PETRUM',20.00,'51516',1,'TESTLABEL'),('ded98978892c4942ba1e0a162af4cbc8','2024-11-17 12:06:52.273687','2024-11-17 12:06:52.273719','ANALYSE GRANULOMETRIQUE',20.00,'61954',0,'TESTLABEL'),('f1838c82eed54eb1b5c72ce8f363718b','2024-11-17 12:06:20.962731','2024-11-17 12:06:20.962748','ANALYSE CHIMIQUE',20.00,'61295',0,'TESTLABEL'),('f77d192a72774efca0985d1c68dc469e','2024-11-07 23:17:17.744987','2024-11-07 23:17:17.745019','Product3',11.00,'6122921',0,'TESTLABEL');
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
INSERT INTO `testapp_profile` VALUES ('6c699c8f51c2450f97ad56df2ab5b034','2024-11-04 21:32:10.191350','2024-11-04 21:32:10.191364','',NULL,NULL,'',4),('8b56a5a0de8444b482cf525fdaba9e24','2024-11-03 21:50:31.599082','2024-11-18 02:11:44.740958','',NULL,NULL,'',3);
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
  UNIQUE KEY `accounting_code` (`accounting_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testapp_supplier`
--

LOCK TABLES `testapp_supplier` WRITE;
/*!40000 ALTER TABLE `testapp_supplier` DISABLE KEYS */;
INSERT INTO `testapp_supplier` VALUES ('064ae3b62a4240eeb15aa524e06f54b3','2024-11-07 23:31:17.162271','2024-11-07 23:31:17.162320','SupplierEn1','2','121212121212122','545d','dsd','sd',1,'KOREWAA',0,1,''),('46d97fc9f81c420588a8a5e96ca0d375','2024-11-17 12:05:31.213249','2024-11-17 12:05:31.213266','LPEE','12345','000000000000000','0000000','BROCOLI','4411281',0,'ESSAIS SUR BRIQUES',60,1,''),('8085978a65694fec888b16ae6903f32a','2024-11-07 23:13:30.092485','2024-11-07 23:13:30.092519','Supplier1','lkhjhkj','654564','545s','CASAb','sasa',0,'aslkjlkj',60,1,'supplier_regulations/Code.pdf'),('c32f2842df63456497a29444adc17768','2024-11-08 00:32:42.821807','2024-11-08 00:32:42.821843','HTS','15165165','111111111111111','6151515','sa56as654','44441',1,'',90,1,'');
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

-- Dump completed on 2024-11-18 14:34:42

```

# django_project

This is a binary file of the type: Binary

# manage.py

```py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

# myproject/__init__.py

```py

```

# myproject/asgi.py

```py
"""
ASGI config for myproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_asgi_application()

```

# myproject/settings.py

```py
"""
Django settings for myproject project.

Generated by 'django-admin startproject' using Django 4.2.16.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o&g&fyebijm#od*5^kky-hr-c!dp+1i4qvp5&v^w=n+1nc=5hp'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

LOGIN_REDIRECT_URL = '/profile/'
LOGOUT_REDIRECT_URL = '/'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'testapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'testapp.middleware.RedirectIfNotLoggedInMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'testapp/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_project',
        'USER': 'django_user',               # Use the new user here
        'PASSWORD': 'DjangoPass123!',        # Use the password created earlier
        'HOST': 'localhost',
        'PORT': '3306',
    }
}



# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "myproject/static"]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

```

# myproject/static/css/styles.css

```css
body {
    font-family: Arial, sans-serif;
}

.navbar-brand {
    font-weight: bold;
}

.footer {
    text-align: center;
    font-size: 0.9em;
}


.modal-scrollable-content {
        max-height: 70vh;  /* Limit modal body height to 70% of the viewport height */
        overflow-y: auto;  /* Add scrolling to modal body if content exceeds max height */
    }

.modal-lg {
        max-width: 90%;  /* Set a wider modal to better accommodate detailed content */
    }

/* Accounting Table Styles */
.accounting-table td, 
.accounting-table th {
    vertical-align: middle;
    padding: 0.75rem;
}

.accounting-table thead th {
    background-color: #343a40;
    color: white;
    border-bottom: 2px solid #454d55;
}

.accounting-table .label-column {
    min-width: 200px;
}

.accounting-table .vat-row {
    background-color: rgba(255, 243, 205, 0.7);
}

.accounting-table .total-row {
    background-color: rgba(209, 236, 241, 0.7);
}

.accounting-table td {
    font-size: 0.95rem;
}

.accounting-table tfoot {
    border-top: 2px solid #dee2e6;
}

.accounting-table tbody tr:hover {
    background-color: rgba(0, 0, 0, 0.075);
}

```

# myproject/static/js/scripts.js

```js
console.log("JavaScript file loaded successfully.");

```

# myproject/urls.py

```py
"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from testapp.views import CustomLoginView, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CustomLoginView.as_view(), name='login'),  # Use custom login view
    path('testapp/', include('testapp.urls')),  # Include the URLs from testapp
    path('profile/', lambda request: render(request, 'profile.html'), name='profile'),  # Profile page
    path('logout/', logout_view, name='logout'),  # Logout view   
]


```

# myproject/wsgi.py

```py
"""
WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()

```

# package.json

```json
{
  "dependencies": {
    "@ai-sdk/openai": "^1.0.4",
    "ai": "^4.0.3"
  }
}

```

# requirements.txt

```txt
asgiref==3.8.1
Django==4.2.16
et_xmlfile==2.0.0
mysqlclient==2.2.5
openpyxl==3.1.5
sqlparse==0.5.1
typing_extensions==4.12.2

```

# staticfiles/admin/css/autocomplete.css

```css
select.admin-autocomplete {
    width: 20em;
}

.select2-container--admin-autocomplete.select2-container {
    min-height: 30px;
}

.select2-container--admin-autocomplete .select2-selection--single,
.select2-container--admin-autocomplete .select2-selection--multiple {
    min-height: 30px;
    padding: 0;
}

.select2-container--admin-autocomplete.select2-container--focus .select2-selection,
.select2-container--admin-autocomplete.select2-container--open .select2-selection {
    border-color: var(--body-quiet-color);
    min-height: 30px;
}

.select2-container--admin-autocomplete.select2-container--focus .select2-selection.select2-selection--single,
.select2-container--admin-autocomplete.select2-container--open .select2-selection.select2-selection--single {
    padding: 0;
}

.select2-container--admin-autocomplete.select2-container--focus .select2-selection.select2-selection--multiple,
.select2-container--admin-autocomplete.select2-container--open .select2-selection.select2-selection--multiple {
    padding: 0;
}

.select2-container--admin-autocomplete .select2-selection--single {
    background-color: var(--body-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
}

.select2-container--admin-autocomplete .select2-selection--single .select2-selection__rendered {
    color: var(--body-fg);
    line-height: 30px;
}

.select2-container--admin-autocomplete .select2-selection--single .select2-selection__clear {
    cursor: pointer;
    float: right;
    font-weight: bold;
}

.select2-container--admin-autocomplete .select2-selection--single .select2-selection__placeholder {
    color: var(--body-quiet-color);
}

.select2-container--admin-autocomplete .select2-selection--single .select2-selection__arrow {
    height: 26px;
    position: absolute;
    top: 1px;
    right: 1px;
    width: 20px;
}

.select2-container--admin-autocomplete .select2-selection--single .select2-selection__arrow b {
    border-color: #888 transparent transparent transparent;
    border-style: solid;
    border-width: 5px 4px 0 4px;
    height: 0;
    left: 50%;
    margin-left: -4px;
    margin-top: -2px;
    position: absolute;
    top: 50%;
    width: 0;
}

.select2-container--admin-autocomplete[dir="rtl"] .select2-selection--single .select2-selection__clear {
    float: left;
}

.select2-container--admin-autocomplete[dir="rtl"] .select2-selection--single .select2-selection__arrow {
    left: 1px;
    right: auto;
}

.select2-container--admin-autocomplete.select2-container--disabled .select2-selection--single {
    background-color: var(--darkened-bg);
    cursor: default;
}

.select2-container--admin-autocomplete.select2-container--disabled .select2-selection--single .select2-selection__clear {
    display: none;
}

.select2-container--admin-autocomplete.select2-container--open .select2-selection--single .select2-selection__arrow b {
    border-color: transparent transparent #888 transparent;
    border-width: 0 4px 5px 4px;
}

.select2-container--admin-autocomplete .select2-selection--multiple {
    background-color: var(--body-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: text;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__rendered {
    box-sizing: border-box;
    list-style: none;
    margin: 0;
    padding: 0 10px 5px 5px;
    width: 100%;
    display: flex;
    flex-wrap: wrap;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__rendered li {
    list-style: none;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__placeholder {
    color: var(--body-quiet-color);
    margin-top: 5px;
    float: left;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__clear {
    cursor: pointer;
    float: right;
    font-weight: bold;
    margin: 5px;
    position: absolute;
    right: 0;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__choice {
    background-color: var(--darkened-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: default;
    float: left;
    margin-right: 5px;
    margin-top: 5px;
    padding: 0 5px;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__choice__remove {
    color: var(--body-quiet-color);
    cursor: pointer;
    display: inline-block;
    font-weight: bold;
    margin-right: 2px;
}

.select2-container--admin-autocomplete .select2-selection--multiple .select2-selection__choice__remove:hover {
    color: var(--body-fg);
}

.select2-container--admin-autocomplete[dir="rtl"] .select2-selection--multiple .select2-selection__choice, .select2-container--admin-autocomplete[dir="rtl"] .select2-selection--multiple .select2-selection__placeholder, .select2-container--admin-autocomplete[dir="rtl"] .select2-selection--multiple .select2-search--inline {
    float: right;
}

.select2-container--admin-autocomplete[dir="rtl"] .select2-selection--multiple .select2-selection__choice {
    margin-left: 5px;
    margin-right: auto;
}

.select2-container--admin-autocomplete[dir="rtl"] .select2-selection--multiple .select2-selection__choice__remove {
    margin-left: 2px;
    margin-right: auto;
}

.select2-container--admin-autocomplete.select2-container--focus .select2-selection--multiple {
    border: solid var(--body-quiet-color) 1px;
    outline: 0;
}

.select2-container--admin-autocomplete.select2-container--disabled .select2-selection--multiple {
    background-color: var(--darkened-bg);
    cursor: default;
}

.select2-container--admin-autocomplete.select2-container--disabled .select2-selection__choice__remove {
    display: none;
}

.select2-container--admin-autocomplete.select2-container--open.select2-container--above .select2-selection--single, .select2-container--admin-autocomplete.select2-container--open.select2-container--above .select2-selection--multiple {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}

.select2-container--admin-autocomplete.select2-container--open.select2-container--below .select2-selection--single, .select2-container--admin-autocomplete.select2-container--open.select2-container--below .select2-selection--multiple {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}

.select2-container--admin-autocomplete .select2-search--dropdown {
    background: var(--darkened-bg);
}

.select2-container--admin-autocomplete .select2-search--dropdown .select2-search__field {
    background: var(--body-bg);
    color: var(--body-fg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
}

.select2-container--admin-autocomplete .select2-search--inline .select2-search__field {
    background: transparent;
    color: var(--body-fg);
    border: none;
    outline: 0;
    box-shadow: none;
    -webkit-appearance: textfield;
}

.select2-container--admin-autocomplete .select2-results > .select2-results__options {
    max-height: 200px;
    overflow-y: auto;
    color: var(--body-fg);
    background: var(--body-bg);
}

.select2-container--admin-autocomplete .select2-results__option[role=group] {
    padding: 0;
}

.select2-container--admin-autocomplete .select2-results__option[aria-disabled=true] {
    color: var(--body-quiet-color);
}

.select2-container--admin-autocomplete .select2-results__option[aria-selected=true] {
    background-color: var(--selected-bg);
    color: var(--body-fg);
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option {
    padding-left: 1em;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__group {
    padding-left: 0;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__option {
    margin-left: -1em;
    padding-left: 2em;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__option .select2-results__option {
    margin-left: -2em;
    padding-left: 3em;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option {
    margin-left: -3em;
    padding-left: 4em;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option {
    margin-left: -4em;
    padding-left: 5em;
}

.select2-container--admin-autocomplete .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option .select2-results__option {
    margin-left: -5em;
    padding-left: 6em;
}

.select2-container--admin-autocomplete .select2-results__option--highlighted[aria-selected] {
    background-color: var(--primary);
    color: var(--primary-fg);
}

.select2-container--admin-autocomplete .select2-results__group {
    cursor: default;
    display: block;
    padding: 6px;
}

```

# staticfiles/admin/css/base.css

```css
/*
    DJANGO Admin styles
*/

/* VARIABLE DEFINITIONS */
html[data-theme="light"],
:root {
    --primary: #79aec8;
    --secondary: #417690;
    --accent: #f5dd5d;
    --primary-fg: #fff;

    --body-fg: #333;
    --body-bg: #fff;
    --body-quiet-color: #666;
    --body-loud-color: #000;

    --header-color: #ffc;
    --header-branding-color: var(--accent);
    --header-bg: var(--secondary);
    --header-link-color: var(--primary-fg);

    --breadcrumbs-fg: #c4dce8;
    --breadcrumbs-link-fg: var(--body-bg);
    --breadcrumbs-bg: var(--primary);

    --link-fg: #417893;
    --link-hover-color: #036;
    --link-selected-fg: #5b80b2;

    --hairline-color: #e8e8e8;
    --border-color: #ccc;

    --error-fg: #ba2121;

    --message-success-bg: #dfd;
    --message-warning-bg: #ffc;
    --message-error-bg: #ffefef;

    --darkened-bg: #f8f8f8; /* A bit darker than --body-bg */
    --selected-bg: #e4e4e4; /* E.g. selected table cells */
    --selected-row: #ffc;

    --button-fg: #fff;
    --button-bg: var(--primary);
    --button-hover-bg: #609ab6;
    --default-button-bg: var(--secondary);
    --default-button-hover-bg: #205067;
    --close-button-bg: #747474;
    --close-button-hover-bg: #333;
    --delete-button-bg: #ba2121;
    --delete-button-hover-bg: #a41515;

    --object-tools-fg: var(--button-fg);
    --object-tools-bg: var(--close-button-bg);
    --object-tools-hover-bg: var(--close-button-hover-bg);

    --font-family-primary:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        system-ui,
        Roboto,
        "Helvetica Neue",
        Arial,
        sans-serif,
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Noto Color Emoji";
    --font-family-monospace:
        ui-monospace,
        Menlo,
        Monaco,
        "Cascadia Mono",
        "Segoe UI Mono",
        "Roboto Mono",
        "Oxygen Mono",
        "Ubuntu Monospace",
        "Source Code Pro",
        "Fira Mono",
        "Droid Sans Mono",
        "Courier New",
        monospace,
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Noto Color Emoji";
}

html, body {
    height: 100%;
}

body {
    margin: 0;
    padding: 0;
    font-size: 0.875rem;
    font-family: var(--font-family-primary);
    color: var(--body-fg);
    background: var(--body-bg);
}

/* LINKS */

a:link, a:visited {
    color: var(--link-fg);
    text-decoration: none;
    transition: color 0.15s, background 0.15s;
}

a:focus, a:hover {
    color: var(--link-hover-color);
}

a:focus {
    text-decoration: underline;
}

a img {
    border: none;
}

a.section:link, a.section:visited {
    color: var(--header-link-color);
    text-decoration: none;
}

a.section:focus, a.section:hover {
    text-decoration: underline;
}

/* GLOBAL DEFAULTS */

p, ol, ul, dl {
    margin: .2em 0 .8em 0;
}

p {
    padding: 0;
    line-height: 140%;
}

h1,h2,h3,h4,h5 {
    font-weight: bold;
}

h1 {
    margin: 0 0 20px;
    font-weight: 300;
    font-size: 1.25rem;
    color: var(--body-quiet-color);
}

h2 {
    font-size: 1rem;
    margin: 1em 0 .5em 0;
}

h2.subhead {
    font-weight: normal;
    margin-top: 0;
}

h3 {
    font-size: 0.875rem;
    margin: .8em 0 .3em 0;
    color: var(--body-quiet-color);
    font-weight: bold;
}

h4 {
    font-size: 0.75rem;
    margin: 1em 0 .8em 0;
    padding-bottom: 3px;
}

h5 {
    font-size: 0.625rem;
    margin: 1.5em 0 .5em 0;
    color: var(--body-quiet-color);
    text-transform: uppercase;
    letter-spacing: 1px;
}

ul > li {
    list-style-type: square;
    padding: 1px 0;
}

li ul {
    margin-bottom: 0;
}

li, dt, dd {
    font-size: 0.8125rem;
    line-height: 1.25rem;
}

dt {
    font-weight: bold;
    margin-top: 4px;
}

dd {
    margin-left: 0;
}

form {
    margin: 0;
    padding: 0;
}

fieldset {
    margin: 0;
    min-width: 0;
    padding: 0;
    border: none;
    border-top: 1px solid var(--hairline-color);
}

blockquote {
    font-size: 0.6875rem;
    color: #777;
    margin-left: 2px;
    padding-left: 10px;
    border-left: 5px solid #ddd;
}

code, pre {
    font-family: var(--font-family-monospace);
    color: var(--body-quiet-color);
    font-size: 0.75rem;
    overflow-x: auto;
}

pre.literal-block {
    margin: 10px;
    background: var(--darkened-bg);
    padding: 6px 8px;
}

code strong {
    color: #930;
}

hr {
    clear: both;
    color: var(--hairline-color);
    background-color: var(--hairline-color);
    height: 1px;
    border: none;
    margin: 0;
    padding: 0;
    line-height: 1px;
}

/* TEXT STYLES & MODIFIERS */

.small {
    font-size: 0.6875rem;
}

.mini {
    font-size: 0.625rem;
}

.help, p.help, form p.help, div.help, form div.help, div.help li {
    font-size: 0.6875rem;
    color: var(--body-quiet-color);
}

div.help ul {
     margin-bottom: 0;
}

.help-tooltip {
    cursor: help;
}

p img, h1 img, h2 img, h3 img, h4 img, td img {
    vertical-align: middle;
}

.quiet, a.quiet:link, a.quiet:visited {
    color: var(--body-quiet-color);
    font-weight: normal;
}

.clear {
    clear: both;
}

.nowrap {
    white-space: nowrap;
}

.hidden {
    display: none !important;
}

/* TABLES */

table {
    border-collapse: collapse;
    border-color: var(--border-color);
}

td, th {
    font-size: 0.8125rem;
    line-height: 1rem;
    border-bottom: 1px solid var(--hairline-color);
    vertical-align: top;
    padding: 8px;
}

th {
    font-weight: 600;
    text-align: left;
}

thead th,
tfoot td {
    color: var(--body-quiet-color);
    padding: 5px 10px;
    font-size: 0.6875rem;
    background: var(--body-bg);
    border: none;
    border-top: 1px solid var(--hairline-color);
    border-bottom: 1px solid var(--hairline-color);
}

tfoot td {
    border-bottom: none;
    border-top: 1px solid var(--hairline-color);
}

thead th.required {
    color: var(--body-loud-color);
}

tr.alt {
    background: var(--darkened-bg);
}

tr:nth-child(odd), .row-form-errors {
    background: var(--body-bg);
}

tr:nth-child(even),
tr:nth-child(even) .errorlist,
tr:nth-child(odd) + .row-form-errors,
tr:nth-child(odd) + .row-form-errors .errorlist {
    background: var(--darkened-bg);
}

/* SORTABLE TABLES */

thead th {
    padding: 5px 10px;
    line-height: normal;
    text-transform: uppercase;
    background: var(--darkened-bg);
}

thead th a:link, thead th a:visited {
    color: var(--body-quiet-color);
}

thead th.sorted {
    background: var(--selected-bg);
}

thead th.sorted .text {
    padding-right: 42px;
}

table thead th .text span {
    padding: 8px 10px;
    display: block;
}

table thead th .text a {
    display: block;
    cursor: pointer;
    padding: 8px 10px;
}

table thead th .text a:focus, table thead th .text a:hover {
    background: var(--selected-bg);
}

thead th.sorted a.sortremove {
    visibility: hidden;
}

table thead th.sorted:hover a.sortremove {
    visibility: visible;
}

table thead th.sorted .sortoptions {
    display: block;
    padding: 9px 5px 0 5px;
    float: right;
    text-align: right;
}

table thead th.sorted .sortpriority {
    font-size: .8em;
    min-width: 12px;
    text-align: center;
    vertical-align: 3px;
    margin-left: 2px;
    margin-right: 2px;
}

table thead th.sorted .sortoptions a {
    position: relative;
    width: 14px;
    height: 14px;
    display: inline-block;
    background: url(../img/sorting-icons.svg) 0 0 no-repeat;
    background-size: 14px auto;
}

table thead th.sorted .sortoptions a.sortremove {
    background-position: 0 0;
}

table thead th.sorted .sortoptions a.sortremove:after {
    content: '\\';
    position: absolute;
    top: -6px;
    left: 3px;
    font-weight: 200;
    font-size: 1.125rem;
    color: var(--body-quiet-color);
}

table thead th.sorted .sortoptions a.sortremove:focus:after,
table thead th.sorted .sortoptions a.sortremove:hover:after {
    color: var(--link-fg);
}

table thead th.sorted .sortoptions a.sortremove:focus,
table thead th.sorted .sortoptions a.sortremove:hover {
    background-position: 0 -14px;
}

table thead th.sorted .sortoptions a.ascending {
    background-position: 0 -28px;
}

table thead th.sorted .sortoptions a.ascending:focus,
table thead th.sorted .sortoptions a.ascending:hover {
    background-position: 0 -42px;
}

table thead th.sorted .sortoptions a.descending {
    top: 1px;
    background-position: 0 -56px;
}

table thead th.sorted .sortoptions a.descending:focus,
table thead th.sorted .sortoptions a.descending:hover {
    background-position: 0 -70px;
}

/* FORM DEFAULTS */

input, textarea, select, .form-row p, form .button {
    margin: 2px 0;
    padding: 2px 3px;
    vertical-align: middle;
    font-family: var(--font-family-primary);
    font-weight: normal;
    font-size: 0.8125rem;
}
.form-row div.help {
    padding: 2px 3px;
}

textarea {
    vertical-align: top;
}

input[type=text], input[type=password], input[type=email], input[type=url],
input[type=number], input[type=tel], textarea, select, .vTextField {
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 5px 6px;
    margin-top: 0;
    color: var(--body-fg);
    background-color: var(--body-bg);
}

input[type=text]:focus, input[type=password]:focus, input[type=email]:focus,
input[type=url]:focus, input[type=number]:focus, input[type=tel]:focus,
textarea:focus, select:focus, .vTextField:focus {
    border-color: var(--body-quiet-color);
}

select {
    height: 1.875rem;
}

select[multiple] {
    /* Allow HTML size attribute to override the height in the rule above. */
    height: auto;
    min-height: 150px;
}

/* FORM BUTTONS */

.button, input[type=submit], input[type=button], .submit-row input, a.button {
    background: var(--button-bg);
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    color: var(--button-fg);
    cursor: pointer;
    transition: background 0.15s;
}

a.button {
    padding: 4px 5px;
}

.button:active, input[type=submit]:active, input[type=button]:active,
.button:focus, input[type=submit]:focus, input[type=button]:focus,
.button:hover, input[type=submit]:hover, input[type=button]:hover {
    background: var(--button-hover-bg);
}

.button[disabled], input[type=submit][disabled], input[type=button][disabled] {
    opacity: 0.4;
}

.button.default, input[type=submit].default, .submit-row input.default {
    border: none;
    font-weight: 400;
    background: var(--default-button-bg);
}

.button.default:active, input[type=submit].default:active,
.button.default:focus, input[type=submit].default:focus,
.button.default:hover, input[type=submit].default:hover {
    background: var(--default-button-hover-bg);
}

.button[disabled].default,
input[type=submit][disabled].default,
input[type=button][disabled].default {
    opacity: 0.4;
}


/* MODULES */

.module {
    border: none;
    margin-bottom: 30px;
    background: var(--body-bg);
}

.module p, .module ul, .module h3, .module h4, .module dl, .module pre {
    padding-left: 10px;
    padding-right: 10px;
}

.module blockquote {
    margin-left: 12px;
}

.module ul, .module ol {
    margin-left: 1.5em;
}

.module h3 {
    margin-top: .6em;
}

.module h2, .module caption, .inline-group h2 {
    margin: 0;
    padding: 8px;
    font-weight: 400;
    font-size: 0.8125rem;
    text-align: left;
    background: var(--primary);
    color: var(--header-link-color);
}

.module caption,
.inline-group h2 {
    font-size: 0.75rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.module table {
    border-collapse: collapse;
}

/* MESSAGES & ERRORS */

ul.messagelist {
    padding: 0;
    margin: 0;
}

ul.messagelist li {
    display: block;
    font-weight: 400;
    font-size: 0.8125rem;
    padding: 10px 10px 10px 65px;
    margin: 0 0 10px 0;
    background: var(--message-success-bg) url(../img/icon-yes.svg) 40px 12px no-repeat;
    background-size: 16px auto;
    color: var(--body-fg);
    word-break: break-word;
}

ul.messagelist li.warning {
    background: var(--message-warning-bg) url(../img/icon-alert.svg) 40px 14px no-repeat;
    background-size: 14px auto;
}

ul.messagelist li.error {
    background: var(--message-error-bg) url(../img/icon-no.svg) 40px 12px no-repeat;
    background-size: 16px auto;
}

.errornote {
    font-size: 0.875rem;
    font-weight: 700;
    display: block;
    padding: 10px 12px;
    margin: 0 0 10px 0;
    color: var(--error-fg);
    border: 1px solid var(--error-fg);
    border-radius: 4px;
    background-color: var(--body-bg);
    background-position: 5px 12px;
    overflow-wrap: break-word;
}

ul.errorlist {
    margin: 0 0 4px;
    padding: 0;
    color: var(--error-fg);
    background: var(--body-bg);
}

ul.errorlist li {
    font-size: 0.8125rem;
    display: block;
    margin-bottom: 4px;
    overflow-wrap: break-word;
}

ul.errorlist li:first-child {
    margin-top: 0;
}

ul.errorlist li a {
    color: inherit;
    text-decoration: underline;
}

td ul.errorlist {
    margin: 0;
    padding: 0;
}

td ul.errorlist li {
    margin: 0;
}

.form-row.errors {
    margin: 0;
    border: none;
    border-bottom: 1px solid var(--hairline-color);
    background: none;
}

.form-row.errors ul.errorlist li {
    padding-left: 0;
}

.errors input, .errors select, .errors textarea,
td ul.errorlist + input, td ul.errorlist + select, td ul.errorlist + textarea {
    border: 1px solid var(--error-fg);
}

.description {
    font-size: 0.75rem;
    padding: 5px 0 0 12px;
}

/* BREADCRUMBS */

div.breadcrumbs {
    background: var(--breadcrumbs-bg);
    padding: 10px 40px;
    border: none;
    color: var(--breadcrumbs-fg);
    text-align: left;
}

div.breadcrumbs a {
    color: var(--breadcrumbs-link-fg);
}

div.breadcrumbs a:focus, div.breadcrumbs a:hover {
    color: var(--breadcrumbs-fg);
}

/* ACTION ICONS */

.viewlink, .inlineviewlink {
    padding-left: 16px;
    background: url(../img/icon-viewlink.svg) 0 1px no-repeat;
}

.addlink {
    padding-left: 16px;
    background: url(../img/icon-addlink.svg) 0 1px no-repeat;
}

.changelink, .inlinechangelink {
    padding-left: 16px;
    background: url(../img/icon-changelink.svg) 0 1px no-repeat;
}

.deletelink {
    padding-left: 16px;
    background: url(../img/icon-deletelink.svg) 0 1px no-repeat;
}

a.deletelink:link, a.deletelink:visited {
    color: #CC3434; /* XXX Probably unused? */
}

a.deletelink:focus, a.deletelink:hover {
    color: #993333; /* XXX Probably unused? */
    text-decoration: none;
}

/* OBJECT TOOLS */

.object-tools {
    font-size: 0.625rem;
    font-weight: bold;
    padding-left: 0;
    float: right;
    position: relative;
    margin-top: -48px;
}

.object-tools li {
    display: block;
    float: left;
    margin-left: 5px;
    height: 1rem;
}

.object-tools a {
    border-radius: 15px;
}

.object-tools a:link, .object-tools a:visited {
    display: block;
    float: left;
    padding: 3px 12px;
    background: var(--object-tools-bg);
    color: var(--object-tools-fg);
    font-weight: 400;
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.object-tools a:focus, .object-tools a:hover {
    background-color: var(--object-tools-hover-bg);
}

.object-tools a:focus{
    text-decoration: none;
}

.object-tools a.viewsitelink, .object-tools a.addlink {
    background-repeat: no-repeat;
    background-position: right 7px center;
    padding-right: 26px;
}

.object-tools a.viewsitelink {
    background-image: url(../img/tooltag-arrowright.svg);
}

.object-tools a.addlink {
    background-image: url(../img/tooltag-add.svg);
}

/* OBJECT HISTORY */

#change-history table {
    width: 100%;
}

#change-history table tbody th {
    width: 16em;
}

#change-history .paginator {
    color: var(--body-quiet-color);
    border-bottom: 1px solid var(--hairline-color);
    background: var(--body-bg);
    overflow: hidden;
}

/* PAGE STRUCTURE */

#container {
    position: relative;
    width: 100%;
    min-width: 980px;
    padding: 0;
    display: flex;
    flex-direction: column;
    height: 100%;
}

#container > div {
    flex-shrink: 0;
}

#container > .main {
    display: flex;
    flex: 1 0 auto;
}

.main > .content {
    flex:  1 0;
    max-width: 100%;
}

.skip-to-content-link {
    position: absolute;
    top: -999px;
    margin: 5px;
    padding: 5px;
    background: var(--body-bg);
    z-index: 1;
}

.skip-to-content-link:focus {
    left: 0px;
    top: 0px;
}

#content {
    padding: 20px 40px;
}

.dashboard #content {
    width: 600px;
}

#content-main {
    float: left;
    width: 100%;
}

#content-related {
    float: right;
    width: 260px;
    position: relative;
    margin-right: -300px;
}

#footer {
    clear: both;
    padding: 10px;
}

/* COLUMN TYPES */

.colMS {
    margin-right: 300px;
}

.colSM {
    margin-left: 300px;
}

.colSM #content-related {
    float: left;
    margin-right: 0;
    margin-left: -300px;
}

.colSM #content-main {
    float: right;
}

.popup .colM {
    width: auto;
}

/* HEADER */

#header {
    width: auto;
    height: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 40px;
    background: var(--header-bg);
    color: var(--header-color);
    overflow: hidden;
}

#header a:link, #header a:visited, #logout-form button {
    color: var(--header-link-color);
}

#header a:focus , #header a:hover {
    text-decoration: underline;
}

#branding {
    display: flex;
}

#branding h1 {
    padding: 0;
    margin: 0;
    margin-inline-end: 20px;
    font-weight: 300;
    font-size: 1.5rem;
    color: var(--header-branding-color);
}

#branding h1 a:link, #branding h1 a:visited {
    color: var(--accent);
}

#branding h2 {
    padding: 0 10px;
    font-size: 0.875rem;
    margin: -8px 0 8px 0;
    font-weight: normal;
    color: var(--header-color);
}

#branding a:hover {
    text-decoration: none;
}

#logout-form {
    display: inline;
}

#logout-form button {
    background: none;
    border: 0;
    cursor: pointer;
    font-family: var(--font-family-primary);
}

#user-tools {
    float: right;
    margin: 0 0 0 20px;
    text-align: right;
}

#user-tools, #logout-form button{
    padding: 0;
    font-weight: 300;
    font-size: 0.6875rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

#user-tools a, #logout-form button {
    border-bottom: 1px solid rgba(255, 255, 255, 0.25);
}

#user-tools a:focus, #user-tools a:hover,
#logout-form button:active, #logout-form button:hover {
    text-decoration: none;
    border-bottom: 0;
}

#logout-form button:active, #logout-form button:hover {
    margin-bottom: 1px;
}

/* SIDEBAR */

#content-related {
    background: var(--darkened-bg);
}

#content-related .module {
    background: none;
}

#content-related h3 {
    color: var(--body-quiet-color);
    padding: 0 16px;
    margin: 0 0 16px;
}

#content-related h4 {
    font-size: 0.8125rem;
}

#content-related p {
    padding-left: 16px;
    padding-right: 16px;
}

#content-related .actionlist {
    padding: 0;
    margin: 16px;
}

#content-related .actionlist li {
    line-height: 1.2;
    margin-bottom: 10px;
    padding-left: 18px;
}

#content-related .module h2 {
    background: none;
    padding: 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--hairline-color);
    font-size: 1.125rem;
    color: var(--body-fg);
}

.delete-confirmation form input[type="submit"] {
    background: var(--delete-button-bg);
    border-radius: 4px;
    padding: 10px 15px;
    color: var(--button-fg);
}

.delete-confirmation form input[type="submit"]:active,
.delete-confirmation form input[type="submit"]:focus,
.delete-confirmation form input[type="submit"]:hover {
    background: var(--delete-button-hover-bg);
}

.delete-confirmation form .cancel-link {
    display: inline-block;
    vertical-align: middle;
    height: 0.9375rem;
    line-height: 0.9375rem;
    border-radius: 4px;
    padding: 10px 15px;
    color: var(--button-fg);
    background: var(--close-button-bg);
    margin: 0 0 0 10px;
}

.delete-confirmation form .cancel-link:active,
.delete-confirmation form .cancel-link:focus,
.delete-confirmation form .cancel-link:hover {
    background: var(--close-button-hover-bg);
}

/* POPUP */
.popup #content {
    padding: 20px;
}

.popup #container {
    min-width: 0;
}

.popup #header {
    padding: 10px 20px;
}

/* PAGINATOR */

.paginator {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8125rem;
    padding-top: 10px;
    padding-bottom: 10px;
    line-height: 22px;
    margin: 0;
    border-top: 1px solid var(--hairline-color);
    width: 100%;
}

.paginator a:link, .paginator a:visited {
    padding: 2px 6px;
    background: var(--button-bg);
    text-decoration: none;
    color: var(--button-fg);
}

.paginator a.showall {
    border: none;
    background: none;
    color: var(--link-fg);
}

.paginator a.showall:focus, .paginator a.showall:hover {
    background: none;
    color: var(--link-hover-color);
}

.paginator .end {
    margin-right: 6px;
}

.paginator .this-page {
    padding: 2px 6px;
    font-weight: bold;
    font-size: 0.8125rem;
    vertical-align: top;
}

.paginator a:focus, .paginator a:hover {
    color: white;
    background: var(--link-hover-color);
}

.paginator input {
    margin-left: auto;
}

.base-svgs {
    display: none;
}

```

# staticfiles/admin/css/changelists.css

```css
/* CHANGELISTS */

#changelist {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}

#changelist .changelist-form-container {
    flex: 1 1 auto;
    min-width: 0;
}

#changelist table {
    width: 100%;
}

.change-list .hiddenfields { display:none; }

.change-list .filtered table {
    border-right: none;
}

.change-list .filtered {
    min-height: 400px;
}

.change-list .filtered .results, .change-list .filtered .paginator,
.filtered #toolbar, .filtered div.xfull {
    width: auto;
}

.change-list .filtered table tbody th {
    padding-right: 1em;
}

#changelist-form .results {
    overflow-x: auto;
    width: 100%;
}

#changelist .toplinks {
    border-bottom: 1px solid var(--hairline-color);
}

#changelist .paginator {
    color: var(--body-quiet-color);
    border-bottom: 1px solid var(--hairline-color);
    background: var(--body-bg);
    overflow: hidden;
}

/* CHANGELIST TABLES */

#changelist table thead th {
    padding: 0;
    white-space: nowrap;
    vertical-align: middle;
}

#changelist table thead th.action-checkbox-column {
    width: 1.5em;
    text-align: center;
}

#changelist table tbody td.action-checkbox {
    text-align: center;
}

#changelist table tfoot {
    color: var(--body-quiet-color);
}

/* TOOLBAR */

#toolbar {
    padding: 8px 10px;
    margin-bottom: 15px;
    border-top: 1px solid var(--hairline-color);
    border-bottom: 1px solid var(--hairline-color);
    background: var(--darkened-bg);
    color: var(--body-quiet-color);
}

#toolbar form input {
    border-radius: 4px;
    font-size: 0.875rem;
    padding: 5px;
    color: var(--body-fg);
}

#toolbar #searchbar {
    height: 1.1875rem;
    border: 1px solid var(--border-color);
    padding: 2px 5px;
    margin: 0;
    vertical-align: top;
    font-size: 0.8125rem;
    max-width: 100%;
}

#toolbar #searchbar:focus {
    border-color: var(--body-quiet-color);
}

#toolbar form input[type="submit"] {
    border: 1px solid var(--border-color);
    font-size: 0.8125rem;
    padding: 4px 8px;
    margin: 0;
    vertical-align: middle;
    background: var(--body-bg);
    box-shadow: 0 -15px 20px -10px rgba(0, 0, 0, 0.15) inset;
    cursor: pointer;
    color: var(--body-fg);
}

#toolbar form input[type="submit"]:focus,
#toolbar form input[type="submit"]:hover {
    border-color: var(--body-quiet-color);
}

#changelist-search img {
    vertical-align: middle;
    margin-right: 4px;
}

#changelist-search .help {
    word-break: break-word;
}

/* FILTER COLUMN */

#changelist-filter {
    flex: 0 0 240px;
    order: 1;
    background: var(--darkened-bg);
    border-left: none;
    margin: 0 0 0 30px;
}

#changelist-filter h2 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 5px 15px;
    margin-bottom: 12px;
    border-bottom: none;
}

#changelist-filter h3,
#changelist-filter details summary {
    font-weight: 400;
    padding: 0 15px;
    margin-bottom: 10px;
}

#changelist-filter details summary > * {
    display: inline;
}

#changelist-filter details > summary {
    list-style-type: none;
}

#changelist-filter details > summary::-webkit-details-marker {
    display: none;
}

#changelist-filter details > summary::before {
    content: '→';
    font-weight: bold;
    color: var(--link-hover-color);
}

#changelist-filter details[open] > summary::before {
    content: '↓';
}

#changelist-filter ul {
    margin: 5px 0;
    padding: 0 15px 15px;
    border-bottom: 1px solid var(--hairline-color);
}

#changelist-filter ul:last-child {
    border-bottom: none;
}

#changelist-filter li {
    list-style-type: none;
    margin-left: 0;
    padding-left: 0;
}

#changelist-filter a {
    display: block;
    color: var(--body-quiet-color);
    word-break: break-word;
}

#changelist-filter li.selected {
    border-left: 5px solid var(--hairline-color);
    padding-left: 10px;
    margin-left: -15px;
}

#changelist-filter li.selected a {
    color: var(--link-selected-fg);
}

#changelist-filter a:focus, #changelist-filter a:hover,
#changelist-filter li.selected a:focus,
#changelist-filter li.selected a:hover {
    color: var(--link-hover-color);
}

#changelist-filter #changelist-filter-clear a {
    font-size: 0.8125rem;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--hairline-color);
}

/* DATE DRILLDOWN */

.change-list .toplinks {
    display: flex;
    padding-bottom: 5px;
    flex-wrap: wrap;
    gap: 3px 17px;
    font-weight: bold;
}

.change-list .toplinks a {
    font-size: 0.8125rem;
}

.change-list .toplinks .date-back {
    color: var(--body-quiet-color);
}

.change-list .toplinks .date-back:focus,
.change-list .toplinks .date-back:hover {
    color: var(--link-hover-color);
}

/* ACTIONS */

.filtered .actions {
    border-right: none;
}

#changelist table input {
    margin: 0;
    vertical-align: baseline;
}

/* Once the :has() pseudo-class is supported by all browsers, the tr.selected
   selector and the JS adding the class can be removed. */
#changelist tbody tr.selected {
    background-color: var(--selected-row);
}

#changelist tbody tr:has(.action-select:checked) {
    background-color: var(--selected-row);
}

#changelist .actions {
    padding: 10px;
    background: var(--body-bg);
    border-top: none;
    border-bottom: none;
    line-height: 1.5rem;
    color: var(--body-quiet-color);
    width: 100%;
}

#changelist .actions span.all,
#changelist .actions span.action-counter,
#changelist .actions span.clear,
#changelist .actions span.question {
    font-size: 0.8125rem;
    margin: 0 0.5em;
}

#changelist .actions:last-child {
    border-bottom: none;
}

#changelist .actions select {
    vertical-align: top;
    height: 1.5rem;
    color: var(--body-fg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.875rem;
    padding: 0 0 0 4px;
    margin: 0;
    margin-left: 10px;
}

#changelist .actions select:focus {
    border-color: var(--body-quiet-color);
}

#changelist .actions label {
    display: inline-block;
    vertical-align: middle;
    font-size: 0.8125rem;
}

#changelist .actions .button {
    font-size: 0.8125rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--body-bg);
    box-shadow: 0 -15px 20px -10px rgba(0, 0, 0, 0.15) inset;
    cursor: pointer;
    height: 1.5rem;
    line-height: 1;
    padding: 4px 8px;
    margin: 0;
    color: var(--body-fg);
}

#changelist .actions .button:focus, #changelist .actions .button:hover {
    border-color: var(--body-quiet-color);
}

```

# staticfiles/admin/css/dark_mode.css

```css
@media (prefers-color-scheme: dark) {
    :root {
      --primary: #264b5d;
      --primary-fg: #f7f7f7;
  
      --body-fg: #eeeeee;
      --body-bg: #121212;
      --body-quiet-color: #e0e0e0;
      --body-loud-color: #ffffff;
  
      --breadcrumbs-link-fg: #e0e0e0;
      --breadcrumbs-bg: var(--primary);
  
      --link-fg: #81d4fa;
      --link-hover-color: #4ac1f7;
      --link-selected-fg: #6f94c6;
  
      --hairline-color: #272727;
      --border-color: #353535;
  
      --error-fg: #e35f5f;
      --message-success-bg: #006b1b;
      --message-warning-bg: #583305;
      --message-error-bg: #570808;
  
      --darkened-bg: #212121;
      --selected-bg: #1b1b1b;
      --selected-row: #00363a;
  
      --close-button-bg: #333333;
      --close-button-hover-bg: #666666;
    }
  }


html[data-theme="dark"] {
    --primary: #264b5d;
    --primary-fg: #f7f7f7;

    --body-fg: #eeeeee;
    --body-bg: #121212;
    --body-quiet-color: #e0e0e0;
    --body-loud-color: #ffffff;

    --breadcrumbs-link-fg: #e0e0e0;
    --breadcrumbs-bg: var(--primary);

    --link-fg: #81d4fa;
    --link-hover-color: #4ac1f7;
    --link-selected-fg: #6f94c6;

    --hairline-color: #272727;
    --border-color: #353535;

    --error-fg: #e35f5f;
    --message-success-bg: #006b1b;
    --message-warning-bg: #583305;
    --message-error-bg: #570808;

    --darkened-bg: #212121;
    --selected-bg: #1b1b1b;
    --selected-row: #00363a;

    --close-button-bg: #333333;
    --close-button-hover-bg: #666666;
}

/* THEME SWITCH */
.theme-toggle {
    cursor: pointer;
    border: none;
    padding: 0;
    background: transparent;
    vertical-align: middle;
    margin-inline-start: 5px;
    margin-top: -1px;
}

.theme-toggle svg {
    vertical-align: middle;
    height: 1rem;
    width: 1rem;
    display: none;
}

/*
Fully hide screen reader text so we only show the one matching the current
theme.
*/
.theme-toggle .visually-hidden {
    display: none;
}

html[data-theme="auto"] .theme-toggle .theme-label-when-auto {
    display: block;
}

html[data-theme="dark"] .theme-toggle .theme-label-when-dark {
    display: block;
}

html[data-theme="light"] .theme-toggle .theme-label-when-light {
    display: block;
}

/* ICONS */
.theme-toggle svg.theme-icon-when-auto,
.theme-toggle svg.theme-icon-when-dark,
.theme-toggle svg.theme-icon-when-light {
    fill: var(--header-link-color);
    color: var(--header-bg);
}

html[data-theme="auto"] .theme-toggle svg.theme-icon-when-auto {
    display: block;
}

html[data-theme="dark"] .theme-toggle svg.theme-icon-when-dark {
    display: block;
}

html[data-theme="light"] .theme-toggle svg.theme-icon-when-light {
    display: block;
}

.visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0,0,0,0);
    white-space: nowrap;
    border: 0;
    color: var(--body-fg);
    background-color: var(--body-bg);
}

```

# staticfiles/admin/css/dashboard.css

```css
/* DASHBOARD */
.dashboard td, .dashboard th {
    word-break: break-word;
}

.dashboard .module table th {
    width: 100%;
}

.dashboard .module table td {
    white-space: nowrap;
}

.dashboard .module table td a {
    display: block;
    padding-right: .6em;
}

/* RECENT ACTIONS MODULE */

.module ul.actionlist {
    margin-left: 0;
}

ul.actionlist li {
    list-style-type: none;
    overflow: hidden;
    text-overflow: ellipsis;
}

```

# staticfiles/admin/css/forms.css

```css
@import url('widgets.css');

/* FORM ROWS */

.form-row {
    overflow: hidden;
    padding: 10px;
    font-size: 0.8125rem;
    border-bottom: 1px solid var(--hairline-color);
}

.form-row img, .form-row input {
    vertical-align: middle;
}

.form-row label input[type="checkbox"] {
    margin-top: 0;
    vertical-align: 0;
}

form .form-row p {
    padding-left: 0;
}

.flex-container {
    display: flex;
}

.form-multiline {
    flex-wrap: wrap;
}

.form-multiline > div {
    padding-bottom: 10px;
}

/* FORM LABELS */

label {
    font-weight: normal;
    color: var(--body-quiet-color);
    font-size: 0.8125rem;
}

.required label, label.required {
    font-weight: bold;
    color: var(--body-fg);
}

/* RADIO BUTTONS */

form div.radiolist div {
    padding-right: 7px;
}

form div.radiolist.inline div {
    display: inline-block;
}

form div.radiolist label {
    width: auto;
}

form div.radiolist input[type="radio"] {
    margin: -2px 4px 0 0;
    padding: 0;
}

form ul.inline {
    margin-left: 0;
    padding: 0;
}

form ul.inline li {
    float: left;
    padding-right: 7px;
}

/* ALIGNED FIELDSETS */

.aligned label {
    display: block;
    padding: 4px 10px 0 0;
    min-width: 160px;
    width: 160px;
    word-wrap: break-word;
    line-height: 1;
}

.aligned label:not(.vCheckboxLabel):after {
    content: '';
    display: inline-block;
    vertical-align: middle;
    height: 1.625rem;
}

.aligned label + p, .aligned .checkbox-row + div.help, .aligned label + div.readonly {
    padding: 6px 0;
    margin-top: 0;
    margin-bottom: 0;
    margin-left: 0;
    overflow-wrap: break-word;
}

.aligned ul label {
    display: inline;
    float: none;
    width: auto;
}

.aligned .form-row input {
    margin-bottom: 0;
}

.colMS .aligned .vLargeTextField, .colMS .aligned .vXMLLargeTextField {
    width: 350px;
}

form .aligned ul {
    margin-left: 160px;
    padding-left: 10px;
}

form .aligned div.radiolist {
    display: inline-block;
    margin: 0;
    padding: 0;
}

form .aligned p.help,
form .aligned div.help {
    margin-top: 0;
    margin-left: 160px;
    padding-left: 10px;
}

form .aligned p.date div.help.timezonewarning,
form .aligned p.datetime div.help.timezonewarning,
form .aligned p.time div.help.timezonewarning {
    margin-left: 0;
    padding-left: 0;
    font-weight: normal;
}

form .aligned p.help:last-child,
form .aligned div.help:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
}

form .aligned input + p.help,
form .aligned textarea + p.help,
form .aligned select + p.help,
form .aligned input + div.help,
form .aligned textarea + div.help,
form .aligned select + div.help {
    margin-left: 160px;
    padding-left: 10px;
}

form .aligned ul li {
    list-style: none;
}

form .aligned table p {
    margin-left: 0;
    padding-left: 0;
}

.aligned .vCheckboxLabel {
    float: none;
    width: auto;
    display: inline-block;
    vertical-align: -3px;
    padding: 0 0 5px 5px;
}

.aligned .vCheckboxLabel + p.help,
.aligned .vCheckboxLabel + div.help {
    margin-top: -4px;
}

.colM .aligned .vLargeTextField, .colM .aligned .vXMLLargeTextField {
    width: 610px;
}

fieldset .fieldBox {
    margin-right: 20px;
}

/* WIDE FIELDSETS */

.wide label {
    width: 200px;
}

form .wide p,
form .wide ul.errorlist,
form .wide input + p.help,
form .wide input + div.help {
    margin-left: 200px;
}

form .wide p.help,
form .wide div.help {
    padding-left: 50px;
}

form div.help ul {
    padding-left: 0;
    margin-left: 0;
}

.colM fieldset.wide .vLargeTextField, .colM fieldset.wide .vXMLLargeTextField {
    width: 450px;
}

/* COLLAPSED FIELDSETS */

fieldset.collapsed * {
    display: none;
}

fieldset.collapsed h2, fieldset.collapsed {
    display: block;
}

fieldset.collapsed {
    border: 1px solid var(--hairline-color);
    border-radius: 4px;
    overflow: hidden;
}

fieldset.collapsed h2 {
    background: var(--darkened-bg);
    color: var(--body-quiet-color);
}

fieldset .collapse-toggle {
    color: var(--header-link-color);
}

fieldset.collapsed .collapse-toggle {
    background: transparent;
    display: inline;
    color: var(--link-fg);
}

/* MONOSPACE TEXTAREAS */

fieldset.monospace textarea {
    font-family: var(--font-family-monospace);
}

/* SUBMIT ROW */

.submit-row {
    padding: 12px 14px 12px;
    margin: 0 0 20px;
    background: var(--darkened-bg);
    border: 1px solid var(--hairline-color);
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

body.popup .submit-row {
    overflow: auto;
}

.submit-row input {
    height: 2.1875rem;
    line-height: 0.9375rem;
}

.submit-row input, .submit-row a {
    margin: 0;
}

.submit-row input.default {
    text-transform: uppercase;
}

.submit-row a.deletelink {
    margin-left: auto;
}

.submit-row a.deletelink {
    display: block;
    background: var(--delete-button-bg);
    border-radius: 4px;
    padding: 0.625rem 0.9375rem;
    height: 0.9375rem;
    line-height: 0.9375rem;
    color: var(--button-fg);
}

.submit-row a.closelink {
    display: inline-block;
    background: var(--close-button-bg);
    border-radius: 4px;
    padding: 10px 15px;
    height: 0.9375rem;
    line-height: 0.9375rem;
    color: var(--button-fg);
}

.submit-row a.deletelink:focus,
.submit-row a.deletelink:hover,
.submit-row a.deletelink:active {
    background: var(--delete-button-hover-bg);
    text-decoration: none;
}

.submit-row a.closelink:focus,
.submit-row a.closelink:hover,
.submit-row a.closelink:active {
    background: var(--close-button-hover-bg);
    text-decoration: none;
}

/* CUSTOM FORM FIELDS */

.vSelectMultipleField {
    vertical-align: top;
}

.vCheckboxField {
    border: none;
}

.vDateField, .vTimeField {
    margin-right: 2px;
    margin-bottom: 4px;
}

.vDateField {
    min-width: 6.85em;
}

.vTimeField {
    min-width: 4.7em;
}

.vURLField {
    width: 30em;
}

.vLargeTextField, .vXMLLargeTextField {
    width: 48em;
}

.flatpages-flatpage #id_content {
    height: 40.2em;
}

.module table .vPositiveSmallIntegerField {
    width: 2.2em;
}

.vIntegerField {
    width: 5em;
}

.vBigIntegerField {
    width: 10em;
}

.vForeignKeyRawIdAdminField {
    width: 5em;
}

.vTextField, .vUUIDField {
    width: 20em;
}

/* INLINES */

.inline-group {
    padding: 0;
    margin: 0 0 30px;
}

.inline-group thead th {
    padding: 8px 10px;
}

.inline-group .aligned label {
    width: 160px;
}

.inline-related {
    position: relative;
}

.inline-related h3 {
    margin: 0;
    color: var(--body-quiet-color);
    padding: 5px;
    font-size: 0.8125rem;
    background: var(--darkened-bg);
    border-top: 1px solid var(--hairline-color);
    border-bottom: 1px solid var(--hairline-color);
}

.inline-related h3 span.delete {
    float: right;
}

.inline-related h3 span.delete label {
    margin-left: 2px;
    font-size: 0.6875rem;
}

.inline-related fieldset {
    margin: 0;
    background: var(--body-bg);
    border: none;
    width: 100%;
}

.inline-related fieldset.module h3 {
    margin: 0;
    padding: 2px 5px 3px 5px;
    font-size: 0.6875rem;
    text-align: left;
    font-weight: bold;
    background: #bcd;
    color: var(--body-bg);
}

.inline-group .tabular fieldset.module {
    border: none;
}

.inline-related.tabular fieldset.module table {
    width: 100%;
    overflow-x: scroll;
}

.last-related fieldset {
    border: none;
}

.inline-group .tabular tr.has_original td {
    padding-top: 2em;
}

.inline-group .tabular tr td.original {
    padding: 2px 0 0 0;
    width: 0;
    _position: relative;
}

.inline-group .tabular th.original {
    width: 0px;
    padding: 0;
}

.inline-group .tabular td.original p {
    position: absolute;
    left: 0;
    height: 1.1em;
    padding: 2px 9px;
    overflow: hidden;
    font-size: 0.5625rem;
    font-weight: bold;
    color: var(--body-quiet-color);
    _width: 700px;
}

.inline-group ul.tools {
    padding: 0;
    margin: 0;
    list-style: none;
}

.inline-group ul.tools li {
    display: inline;
    padding: 0 5px;
}

.inline-group div.add-row,
.inline-group .tabular tr.add-row td {
    color: var(--body-quiet-color);
    background: var(--darkened-bg);
    padding: 8px 10px;
    border-bottom: 1px solid var(--hairline-color);
}

.inline-group .tabular tr.add-row td {
    padding: 8px 10px;
    border-bottom: 1px solid var(--hairline-color);
}

.inline-group ul.tools a.add,
.inline-group div.add-row a,
.inline-group .tabular tr.add-row td a {
    background: url(../img/icon-addlink.svg) 0 1px no-repeat;
    padding-left: 16px;
    font-size: 0.75rem;
}

.empty-form {
    display: none;
}

/* RELATED FIELD ADD ONE / LOOKUP */

.related-lookup {
    margin-left: 5px;
    display: inline-block;
    vertical-align: middle;
    background-repeat: no-repeat;
    background-size: 14px;
}

.related-lookup {
    width: 1rem;
    height: 1rem;
    background-image: url(../img/search.svg);
}

form .related-widget-wrapper ul {
    display: inline-block;
    margin-left: 0;
    padding-left: 0;
}

.clearable-file-input input {
    margin-top: 0;
}

```

# staticfiles/admin/css/login.css

```css
/* LOGIN FORM */

.login {
    background: var(--darkened-bg);
    height: auto;
}

.login #header {
    height: auto;
    padding: 15px 16px;
    justify-content: center;
}

.login #header h1 {
    font-size: 1.125rem;
    margin: 0;
}

.login #header h1 a {
    color: var(--header-link-color);
}

.login #content {
    padding: 20px 20px 0;
}

.login #container {
    background: var(--body-bg);
    border: 1px solid var(--hairline-color);
    border-radius: 4px;
    overflow: hidden;
    width: 28em;
    min-width: 300px;
    margin: 100px auto;
    height: auto;
}

.login .form-row {
    padding: 4px 0;
}

.login .form-row label {
    display: block;
    line-height: 2em;
}

.login .form-row #id_username, .login .form-row #id_password {
    padding: 8px;
    width: 100%;
    box-sizing: border-box;
}

.login .submit-row {
    padding: 1em 0 0 0;
    margin: 0;
    text-align: center;
}

.login .password-reset-link {
    text-align: center;
}

```

# staticfiles/admin/css/nav_sidebar.css

```css
.sticky {
    position: sticky;
    top: 0;
    max-height: 100vh;
}

.toggle-nav-sidebar {
    z-index: 20;
    left: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 23px;
    width: 23px;
    border: 0;
    border-right: 1px solid var(--hairline-color);
    background-color: var(--body-bg);
    cursor: pointer;
    font-size: 1.25rem;
    color: var(--link-fg);
    padding: 0;
}

[dir="rtl"] .toggle-nav-sidebar {
    border-left: 1px solid var(--hairline-color);
    border-right: 0;
}

.toggle-nav-sidebar:hover,
.toggle-nav-sidebar:focus {
    background-color: var(--darkened-bg);
}

#nav-sidebar {
    z-index: 15;
    flex: 0 0 275px;
    left: -276px;
    margin-left: -276px;
    border-top: 1px solid transparent;
    border-right: 1px solid var(--hairline-color);
    background-color: var(--body-bg);
    overflow: auto;
}

[dir="rtl"] #nav-sidebar {
    border-left: 1px solid var(--hairline-color);
    border-right: 0;
    left: 0;
    margin-left: 0;
    right: -276px;
    margin-right: -276px;
}

.toggle-nav-sidebar::before {
    content: '\00BB';
}

.main.shifted .toggle-nav-sidebar::before {
    content: '\00AB';
}

.main > #nav-sidebar {
    visibility: hidden;
}

.main.shifted > #nav-sidebar {
    margin-left: 0;
    visibility: visible;
}

[dir="rtl"] .main.shifted > #nav-sidebar {
    margin-right: 0;
}

#nav-sidebar .module th {
    width: 100%;
    overflow-wrap: anywhere;
}

#nav-sidebar .module th,
#nav-sidebar .module caption {
    padding-left: 16px;
}

#nav-sidebar .module td {
    white-space: nowrap;
}

[dir="rtl"] #nav-sidebar .module th,
[dir="rtl"] #nav-sidebar .module caption {
    padding-left: 8px;
    padding-right: 16px;
}

#nav-sidebar .current-app .section:link,
#nav-sidebar .current-app .section:visited {
    color: var(--header-color);
    font-weight: bold;
}

#nav-sidebar .current-model {
    background: var(--selected-row);
}

.main > #nav-sidebar + .content {
    max-width: calc(100% - 23px);
}

.main.shifted > #nav-sidebar + .content {
    max-width: calc(100% - 299px);
}

@media (max-width: 767px) {
    #nav-sidebar, #toggle-nav-sidebar {
        display: none;
    }

    .main > #nav-sidebar + .content,
    .main.shifted > #nav-sidebar + .content {
        max-width: 100%;
    }
}

#nav-filter {
    width: 100%;
    box-sizing: border-box;
    padding: 2px 5px;
    margin: 5px 0;
    border: 1px solid var(--border-color);
    background-color: var(--darkened-bg);
    color: var(--body-fg);
}

#nav-filter:focus {
    border-color: var(--body-quiet-color);
}

#nav-filter.no-results {
    background: var(--message-error-bg);
}

#nav-sidebar table {
    width: 100%;
}

```

# staticfiles/admin/css/responsive_rtl.css

```css
/* TABLETS */

@media (max-width: 1024px) {
    [dir="rtl"] .colMS {
        margin-right: 0;
    }

    [dir="rtl"] #user-tools {
        text-align: right;
    }

    [dir="rtl"] #changelist .actions label {
        padding-left: 10px;
        padding-right: 0;
    }

    [dir="rtl"] #changelist .actions select {
        margin-left: 0;
        margin-right: 15px;
    }

    [dir="rtl"] .change-list .filtered .results,
    [dir="rtl"] .change-list .filtered .paginator,
    [dir="rtl"] .filtered #toolbar,
    [dir="rtl"] .filtered div.xfull,
    [dir="rtl"] .filtered .actions,
    [dir="rtl"] #changelist-filter {
        margin-left: 0;
    }

    [dir="rtl"] .inline-group ul.tools a.add,
    [dir="rtl"] .inline-group div.add-row a,
    [dir="rtl"] .inline-group .tabular tr.add-row td a {
        padding: 8px 26px 8px 10px;
        background-position: calc(100% - 8px) 9px;
    }

    [dir="rtl"] .related-widget-wrapper-link + .selector {
        margin-right: 0;
        margin-left: 15px;
    }

    [dir="rtl"] .selector .selector-filter label {
        margin-right: 0;
        margin-left: 8px;
    }

    [dir="rtl"] .object-tools li {
        float: right;
    }

    [dir="rtl"] .object-tools li + li {
        margin-left: 0;
        margin-right: 15px;
    }

    [dir="rtl"] .dashboard .module table td a {
        padding-left: 0;
        padding-right: 16px;
    }
}

/* MOBILE */

@media (max-width: 767px) {
    [dir="rtl"] .aligned .related-lookup,
    [dir="rtl"] .aligned .datetimeshortcuts {
        margin-left: 0;
        margin-right: 15px;
    }

    [dir="rtl"] .aligned ul,
    [dir="rtl"] form .aligned ul.errorlist {
        margin-right: 0;
    }

    [dir="rtl"] #changelist-filter {
        margin-left: 0;
        margin-right: 0;
    }
    [dir="rtl"] .aligned .vCheckboxLabel {
        padding: 1px 5px 0 0;
    }
}

```

# staticfiles/admin/css/responsive.css

```css
/* Tablets */

input[type="submit"], button {
    -webkit-appearance: none;
    appearance: none;
}

@media (max-width: 1024px) {
    /* Basic */

    html {
        -webkit-text-size-adjust: 100%;
    }

    td, th {
        padding: 10px;
        font-size: 0.875rem;
    }

    .small {
        font-size: 0.75rem;
    }

    /* Layout */

    #container {
        min-width: 0;
    }

    #content {
        padding: 15px 20px 20px;
    }

    div.breadcrumbs {
        padding: 10px 30px;
    }

    /* Header */

    #header {
        flex-direction: column;
        padding: 15px 30px;
        justify-content: flex-start;
    }

    #branding h1 {
        margin: 0 0 8px;
        line-height: 1.2;
    }

    #user-tools {
        margin: 0;
        font-weight: 400;
        line-height: 1.85;
        text-align: left;
    }

    #user-tools a {
        display: inline-block;
        line-height: 1.4;
    }

    /* Dashboard */

    .dashboard #content {
        width: auto;
    }

    #content-related {
        margin-right: -290px;
    }

    .colSM #content-related {
        margin-left: -290px;
    }

    .colMS {
        margin-right: 290px;
    }

    .colSM {
        margin-left: 290px;
    }

    .dashboard .module table td a {
        padding-right: 0;
    }

    td .changelink, td .addlink {
        font-size: 0.8125rem;
    }

    /* Changelist */

    #toolbar {
        border: none;
        padding: 15px;
    }

    #changelist-search > div {
        display: flex;
        flex-wrap: nowrap;
        max-width: 480px;
    }

    #changelist-search label {
        line-height: 1.375rem;
    }

    #toolbar form #searchbar {
        flex: 1 0 auto;
        width: 0;
        height: 1.375rem;
        margin: 0 10px 0 6px;
    }

    #toolbar form input[type=submit] {
        flex: 0 1 auto;
    }

    #changelist-search .quiet {
        width: 0;
        flex: 1 0 auto;
        margin: 5px 0 0 25px;
    }

    #changelist .actions {
        display: flex;
        flex-wrap: wrap;
        padding: 15px 0;
    }

    #changelist .actions label {
        display: flex;
    }

    #changelist .actions select {
        background: var(--body-bg);
    }

    #changelist .actions .button {
        min-width: 48px;
        margin: 0 10px;
    }

    #changelist .actions span.all,
    #changelist .actions span.clear,
    #changelist .actions span.question,
    #changelist .actions span.action-counter {
        font-size: 0.6875rem;
        margin: 0 10px 0 0;
    }

    #changelist-filter {
        flex-basis: 200px;
    }

    .change-list .filtered .results,
    .change-list .filtered .paginator,
    .filtered #toolbar,
    .filtered .actions,

    #changelist .paginator {
        border-top-color: var(--hairline-color); /* XXX Is this used at all? */
    }

    #changelist .results + .paginator {
        border-top: none;
    }

    /* Forms */

    label {
        font-size: 0.875rem;
    }

    .form-row input[type=text],
    .form-row input[type=password],
    .form-row input[type=email],
    .form-row input[type=url],
    .form-row input[type=tel],
    .form-row input[type=number],
    .form-row textarea,
    .form-row select,
    .form-row .vTextField {
        box-sizing: border-box;
        margin: 0;
        padding: 6px 8px;
        min-height: 2.25rem;
        font-size: 0.875rem;
    }

    .form-row select {
        height: 2.25rem;
    }

    .form-row select[multiple] {
        height: auto;
        min-height: 0;
    }

    fieldset .fieldBox + .fieldBox {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--hairline-color);
    }

    textarea {
        max-width: 100%;
        max-height: 120px;
    }

    .aligned label {
        padding-top: 6px;
    }

    .aligned .related-lookup,
    .aligned .datetimeshortcuts,
    .aligned .related-lookup + strong {
        align-self: center;
        margin-left: 15px;
    }

    form .aligned div.radiolist {
        margin-left: 2px;
    }

    .submit-row {
        padding: 8px;
    }

    .submit-row a.deletelink {
        padding: 10px 7px;
    }

    .button, input[type=submit], input[type=button], .submit-row input, a.button {
        padding: 7px;
    }

    /* Related widget */

    .related-widget-wrapper {
        float: none;
    }

    .related-widget-wrapper-link + .selector {
        max-width: calc(100% - 30px);
        margin-right: 15px;
    }

    select + .related-widget-wrapper-link,
    .related-widget-wrapper-link + .related-widget-wrapper-link {
        margin-left: 10px;
    }

    /* Selector */

    .selector {
        display: flex;
        width: 100%;
    }

    .selector .selector-filter {
        display: flex;
        align-items: center;
    }

    .selector .selector-filter label {
        margin: 0 8px 0 0;
    }

    .selector .selector-filter input {
        width: auto;
        min-height: 0;
        flex: 1 1;
    }

    .selector-available, .selector-chosen {
        width: auto;
        flex: 1 1;
        display: flex;
        flex-direction: column;
    }

    .selector select {
        width: 100%;
        flex: 1 0 auto;
        margin-bottom: 5px;
    }

    .selector ul.selector-chooser {
        width: 26px;
        height: 52px;
        padding: 2px 0;
        margin: auto 15px;
        border-radius: 20px;
        transform: translateY(-10px);
    }

    .selector-add, .selector-remove {
        width: 20px;
        height: 20px;
        background-size: 20px auto;
    }

    .selector-add {
        background-position: 0 -120px;
    }

    .selector-remove {
        background-position: 0 -80px;
    }

    a.selector-chooseall, a.selector-clearall {
        align-self: center;
    }

    .stacked {
        flex-direction: column;
        max-width: 480px;
    }

    .stacked > * {
        flex: 0 1 auto;
    }

    .stacked select {
        margin-bottom: 0;
    }

    .stacked .selector-available, .stacked .selector-chosen {
        width: auto;
    }

    .stacked ul.selector-chooser {
        width: 52px;
        height: 26px;
        padding: 0 2px;
        margin: 15px auto;
        transform: none;
    }

    .stacked .selector-chooser li {
        padding: 3px;
    }

    .stacked .selector-add, .stacked .selector-remove {
        background-size: 20px auto;
    }

    .stacked .selector-add {
        background-position: 0 -40px;
    }

    .stacked .active.selector-add {
        background-position: 0 -40px;
    }

    .active.selector-add:focus, .active.selector-add:hover {
        background-position: 0 -140px;
    }

    .stacked .active.selector-add:focus, .stacked .active.selector-add:hover {
        background-position: 0 -60px;
    }

    .stacked .selector-remove {
        background-position: 0 0;
    }

    .stacked .active.selector-remove {
        background-position: 0 0;
    }

    .active.selector-remove:focus, .active.selector-remove:hover {
        background-position: 0 -100px;
    }

    .stacked .active.selector-remove:focus, .stacked .active.selector-remove:hover {
        background-position: 0 -20px;
    }

    .help-tooltip, .selector .help-icon {
        display: none;
    }

    .datetime input {
        width: 50%;
        max-width: 120px;
    }

    .datetime span {
        font-size: 0.8125rem;
    }

    .datetime .timezonewarning {
        display: block;
        font-size: 0.6875rem;
        color: var(--body-quiet-color);
    }

    .datetimeshortcuts {
        color: var(--border-color); /* XXX Redundant, .datetime span also sets #ccc */
    }

    .form-row .datetime input.vDateField, .form-row .datetime input.vTimeField {
        width: 75%;
    }

    .inline-group {
        overflow: auto;
    }

    /* Messages */

    ul.messagelist li {
        padding-left: 55px;
        background-position: 30px 12px;
    }

    ul.messagelist li.error {
        background-position: 30px 12px;
    }

    ul.messagelist li.warning {
        background-position: 30px 14px;
    }

    /* Login */

    .login #header {
        padding: 15px 20px;
    }

    .login #branding h1 {
        margin: 0;
    }

    /* GIS */

    div.olMap {
        max-width: calc(100vw - 30px);
        max-height: 300px;
    }

    .olMap + .clear_features {
        display: block;
        margin-top: 10px;
    }

    /* Docs */

    .module table.xfull {
        width: 100%;
    }

    pre.literal-block {
        overflow: auto;
    }
}

/* Mobile */

@media (max-width: 767px) {
    /* Layout */

    #header, #content, #footer {
        padding: 15px;
    }

    #footer:empty {
        padding: 0;
    }

    div.breadcrumbs {
        padding: 10px 15px;
    }

    /* Dashboard */

    .colMS, .colSM {
        margin: 0;
    }

    #content-related, .colSM #content-related {
        width: 100%;
        margin: 0;
    }

    #content-related .module {
        margin-bottom: 0;
    }

    #content-related .module h2 {
        padding: 10px 15px;
        font-size: 1rem;
    }

    /* Changelist */

    #changelist {
        align-items: stretch;
        flex-direction: column;
    }

    #toolbar {
        padding: 10px;
    }

    #changelist-filter {
        margin-left: 0;
    }

    #changelist .actions label {
        flex: 1 1;
    }

    #changelist .actions select {
        flex: 1 0;
        width: 100%;
    }

    #changelist .actions span {
        flex: 1 0 100%;
    }

    #changelist-filter {
        position: static;
        width: auto;
        margin-top: 30px;
    }

    .object-tools {
        float: none;
        margin: 0 0 15px;
        padding: 0;
        overflow: hidden;
    }

    .object-tools li {
        height: auto;
        margin-left: 0;
    }

    .object-tools li + li {
        margin-left: 15px;
    }

    /* Forms */

    .form-row {
        padding: 15px 0;
    }

    .aligned .form-row,
    .aligned .form-row > div {
        max-width: 100vw;
    }

    .aligned .form-row > div {
        width: calc(100vw - 30px);
    }

    .flex-container {
        flex-flow: column;
    }

    .flex-container.checkbox-row {
        flex-flow: row;
    }

    textarea {
        max-width: none;
    }

    .vURLField {
        width: auto;
    }

    fieldset .fieldBox + .fieldBox {
        margin-top: 15px;
        padding-top: 15px;
    }

    fieldset.collapsed .form-row {
        display: none;
    }

    .aligned label {
        width: 100%;
        min-width: auto;
        padding: 0 0 10px;
    }

    .aligned label:after {
        max-height: 0;
    }

    .aligned .form-row input,
    .aligned .form-row select,
    .aligned .form-row textarea {
        flex: 1 1 auto;
        max-width: 100%;
    }

    .aligned .checkbox-row input {
        flex: 0 1 auto;
        margin: 0;
    }

    .aligned .vCheckboxLabel {
        flex: 1 0;
        padding: 1px 0 0 5px;
    }

    .aligned label + p,
    .aligned label + div.help,
    .aligned label + div.readonly {
        padding: 0;
        margin-left: 0;
    }

    .aligned p.file-upload {
        font-size: 0.8125rem;
    }

    span.clearable-file-input {
        margin-left: 15px;
    }

    span.clearable-file-input label {
        font-size: 0.8125rem;
        padding-bottom: 0;
    }

    .aligned .timezonewarning {
        flex: 1 0 100%;
        margin-top: 5px;
    }

    form .aligned .form-row div.help {
        width: 100%;
        margin: 5px 0 0;
        padding: 0;
    }

    form .aligned ul,
    form .aligned ul.errorlist {
        margin-left: 0;
        padding-left: 0;
    }

    form .aligned div.radiolist {
        margin-top: 5px;
        margin-right: 15px;
        margin-bottom: -3px;
    }

    form .aligned div.radiolist:not(.inline) div + div {
        margin-top: 5px;
    }

    /* Related widget */

    .related-widget-wrapper {
        width: 100%;
        display: flex;
        align-items: flex-start;
    }

    .related-widget-wrapper .selector {
        order: 1;
    }

    .related-widget-wrapper > a {
        order: 2;
    }

    .related-widget-wrapper .radiolist ~ a {
        align-self: flex-end;
    }

    .related-widget-wrapper > select ~ a {
        align-self: center;
    }

    select + .related-widget-wrapper-link,
    .related-widget-wrapper-link + .related-widget-wrapper-link {
        margin-left: 15px;
    }

    /* Selector */

    .selector {
        flex-direction: column;
    }

    .selector > * {
        float: none;
    }

    .selector-available, .selector-chosen {
        margin-bottom: 0;
        flex: 1 1 auto;
    }

    .selector select {
        max-height: 96px;
    }

    .selector ul.selector-chooser {
        display: block;
        float: none;
        width: 52px;
        height: 26px;
        padding: 0 2px;
        margin: 15px auto 20px;
        transform: none;
    }

    .selector ul.selector-chooser li {
        float: left;
    }

    .selector-remove {
        background-position: 0 0;
    }

    .active.selector-remove:focus, .active.selector-remove:hover {
        background-position: 0 -20px;
    }

    .selector-add  {
        background-position: 0 -40px;
    }

    .active.selector-add:focus, .active.selector-add:hover {
        background-position: 0 -60px;
    }

    /* Inlines */

    .inline-group[data-inline-type="stacked"] .inline-related {
        border: 1px solid var(--hairline-color);
        border-radius: 4px;
        margin-top: 15px;
        overflow: auto;
    }

    .inline-group[data-inline-type="stacked"] .inline-related > * {
        box-sizing: border-box;
    }

    .inline-group[data-inline-type="stacked"] .inline-related .module {
        padding: 0 10px;
    }

    .inline-group[data-inline-type="stacked"] .inline-related .module .form-row {
        border-top: 1px solid var(--hairline-color);
        border-bottom: none;
    }

    .inline-group[data-inline-type="stacked"] .inline-related .module .form-row:first-child {
        border-top: none;
    }

    .inline-group[data-inline-type="stacked"] .inline-related h3 {
        padding: 10px;
        border-top-width: 0;
        border-bottom-width: 2px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
    }

    .inline-group[data-inline-type="stacked"] .inline-related h3 .inline_label {
        margin-right: auto;
    }

    .inline-group[data-inline-type="stacked"] .inline-related h3 span.delete {
        float: none;
        flex: 1 1 100%;
        margin-top: 5px;
    }

    .inline-group[data-inline-type="stacked"] .aligned .form-row > div:not([class]) {
        width: 100%;
    }

    .inline-group[data-inline-type="stacked"] .aligned label {
        width: 100%;
    }

    .inline-group[data-inline-type="stacked"] div.add-row {
        margin-top: 15px;
        border: 1px solid var(--hairline-color);
        border-radius: 4px;
    }

    .inline-group div.add-row,
    .inline-group .tabular tr.add-row td {
        padding: 0;
    }

    .inline-group div.add-row a,
    .inline-group .tabular tr.add-row td a {
        display: block;
        padding: 8px 10px 8px 26px;
        background-position: 8px 9px;
    }

    /* Submit row */

    .submit-row {
        padding: 10px;
        margin: 0 0 15px;
        flex-direction: column;
        gap: 8px;
    }

    .submit-row input, .submit-row input.default, .submit-row a {
        text-align: center;
    }

    .submit-row a.closelink {
        padding: 10px 0;
        text-align: center;
    }

    .submit-row a.deletelink {
        margin: 0;
    }

    /* Messages */

    ul.messagelist li {
        padding-left: 40px;
        background-position: 15px 12px;
    }

    ul.messagelist li.error {
        background-position: 15px 12px;
    }

    ul.messagelist li.warning {
        background-position: 15px 14px;
    }

    /* Paginator */

    .paginator .this-page, .paginator a:link, .paginator a:visited {
        padding: 4px 10px;
    }

    /* Login */

    body.login {
        padding: 0 15px;
    }

    .login #container {
        width: auto;
        max-width: 480px;
        margin: 50px auto;
    }

    .login #header,
    .login #content {
        padding: 15px;
    }

    .login #content-main {
        float: none;
    }

    .login .form-row {
        padding: 0;
    }

    .login .form-row + .form-row {
        margin-top: 15px;
    }

    .login .form-row label {
        margin: 0 0 5px;
        line-height: 1.2;
    }

    .login .submit-row {
        padding: 15px 0 0;
    }

    .login br {
        display: none;
    }

    .login .submit-row input {
        margin: 0;
        text-transform: uppercase;
    }

    .errornote {
        margin: 0 0 20px;
        padding: 8px 12px;
        font-size: 0.8125rem;
    }

    /* Calendar and clock */

    .calendarbox, .clockbox {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%);
        margin: 0;
        border: none;
        overflow: visible;
    }

    .calendarbox:before, .clockbox:before {
        content: '';
        position: fixed;
        top: 50%;
        left: 50%;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.75);
        transform: translate(-50%, -50%);
    }

    .calendarbox > *, .clockbox > * {
        position: relative;
        z-index: 1;
    }

    .calendarbox > div:first-child {
        z-index: 2;
    }

    .calendarbox .calendar, .clockbox h2 {
        border-radius: 4px 4px 0 0;
        overflow: hidden;
    }

    .calendarbox .calendar-cancel, .clockbox .calendar-cancel {
        border-radius: 0 0 4px 4px;
        overflow: hidden;
    }

    .calendar-shortcuts {
        padding: 10px 0;
        font-size: 0.75rem;
        line-height: 0.75rem;
    }

    .calendar-shortcuts a {
        margin: 0 4px;
    }

    .timelist a {
        background: var(--body-bg);
        padding: 4px;
    }

    .calendar-cancel {
        padding: 8px 10px;
    }

    .clockbox h2 {
        padding: 8px 15px;
    }

    .calendar caption {
        padding: 10px;
    }

    .calendarbox .calendarnav-previous, .calendarbox .calendarnav-next {
        z-index: 1;
        top: 10px;
    }

    /* History */

    table#change-history tbody th, table#change-history tbody td {
        font-size: 0.8125rem;
        word-break: break-word;
    }

    table#change-history tbody th {
        width: auto;
    }

    /* Docs */

    table.model tbody th, table.model tbody td {
        font-size: 0.8125rem;
        word-break: break-word;
    }
}

```

# staticfiles/admin/css/rtl.css

```css
/* GLOBAL */

th {
    text-align: right;
}

.module h2, .module caption {
    text-align: right;
}

.module ul, .module ol {
    margin-left: 0;
    margin-right: 1.5em;
}

.viewlink, .addlink, .changelink {
    padding-left: 0;
    padding-right: 16px;
    background-position: 100% 1px;
}

.deletelink {
    padding-left: 0;
    padding-right: 16px;
    background-position: 100% 1px;
}

.object-tools {
    float: left;
}

thead th:first-child,
tfoot td:first-child {
    border-left: none;
}

/* LAYOUT */

#user-tools {
    right: auto;
    left: 0;
    text-align: left;
}

div.breadcrumbs {
    text-align: right;
}

#content-main {
    float: right;
}

#content-related {
    float: left;
    margin-left: -300px;
    margin-right: auto;
}

.colMS {
    margin-left: 300px;
    margin-right: 0;
}

/* SORTABLE TABLES */

table thead th.sorted .sortoptions {
   float: left;
}

thead th.sorted .text {
    padding-right: 0;
    padding-left: 42px;
}

/* dashboard styles */

.dashboard .module table td a {
    padding-left: .6em;
    padding-right: 16px;
}

/* changelists styles */

.change-list .filtered table {
    border-left: none;
    border-right: 0px none;
}

#changelist-filter {
    border-left: none;
    border-right: none;
    margin-left: 0;
    margin-right: 30px;
}

#changelist-filter li.selected {
    border-left: none;
    padding-left: 10px;
    margin-left: 0;
    border-right: 5px solid var(--hairline-color);
    padding-right: 10px;
    margin-right: -15px;
}

#changelist table tbody td:first-child, #changelist table tbody th:first-child {
    border-right: none;
    border-left: none;
}

.paginator .end {
    margin-left: 6px;
    margin-right: 0;
}

.paginator input {
    margin-left: 0;
    margin-right: auto;
}

/* FORMS */

.aligned label {
    padding: 0 0 3px 1em;
}

.submit-row a.deletelink {
    margin-left: 0;
    margin-right: auto;
}

.vDateField, .vTimeField {
    margin-left: 2px;
}

.aligned .form-row input {
    margin-left: 5px;
}

form .aligned ul {
    margin-right: 163px;
    padding-right: 10px;
    margin-left: 0;
    padding-left: 0;
}

form ul.inline li {
    float: right;
    padding-right: 0;
    padding-left: 7px;
}

form .aligned p.help,
form .aligned div.help {
    margin-right: 160px;
    padding-right: 10px;
}

form div.help ul,
form .aligned .checkbox-row + .help,
form .aligned p.date div.help.timezonewarning,
form .aligned p.datetime div.help.timezonewarning,
form .aligned p.time div.help.timezonewarning {
    margin-right: 0;
    padding-right: 0;
}

form .wide p.help, form .wide div.help {
    padding-left: 0;
    padding-right: 50px;
}

form .wide p,
form .wide ul.errorlist,
form .wide input + p.help,
form .wide input + div.help {
    margin-right: 200px;
    margin-left: 0px;
}

.submit-row {
    text-align: right;
}

fieldset .fieldBox {
    margin-left: 20px;
    margin-right: 0;
}

.errorlist li {
    background-position: 100% 12px;
    padding: 0;
}

.errornote {
    background-position: 100% 12px;
    padding: 10px 12px;
}

/* WIDGETS */

.calendarnav-previous {
    top: 0;
    left: auto;
    right: 10px;
    background: url(../img/calendar-icons.svg) 0 -30px no-repeat;
}

.calendarbox .calendarnav-previous:focus,
.calendarbox .calendarnav-previous:hover {
    background-position: 0 -45px;
}

.calendarnav-next {
    top: 0;
    right: auto;
    left: 10px;
    background: url(../img/calendar-icons.svg) 0 0 no-repeat;
}

.calendarbox .calendarnav-next:focus,
.calendarbox .calendarnav-next:hover {
    background-position: 0 -15px;
}

.calendar caption, .calendarbox h2 {
    text-align: center;
}

.selector {
    float: right;
}

.selector .selector-filter {
    text-align: right;
}

.selector-add {
  background: url(../img/selector-icons.svg) 0 -64px no-repeat;
}

.active.selector-add:focus, .active.selector-add:hover {
  background-position: 0 -80px;
}

.selector-remove {
  background: url(../img/selector-icons.svg) 0 -96px no-repeat;
}

.active.selector-remove:focus, .active.selector-remove:hover {
  background-position: 0 -112px;
}

a.selector-chooseall {
    background: url(../img/selector-icons.svg) right -128px no-repeat;
}

a.active.selector-chooseall:focus, a.active.selector-chooseall:hover {
    background-position: 100% -144px;
}

a.selector-clearall {
    background: url(../img/selector-icons.svg) 0 -160px no-repeat;
}

a.active.selector-clearall:focus, a.active.selector-clearall:hover {
    background-position: 0 -176px;
}

.inline-deletelink {
    float: left;
}

form .form-row p.datetime {
    overflow: hidden;
}

.related-widget-wrapper {
    float: right;
}

/* MISC */

.inline-related h2, .inline-group h2 {
    text-align: right
}

.inline-related h3 span.delete {
    padding-right: 20px;
    padding-left: inherit;
    left: 10px;
    right: inherit;
    float:left;
}

.inline-related h3 span.delete label {
    margin-left: inherit;
    margin-right: 2px;
}

```

# staticfiles/admin/css/widgets.css

```css
/* SELECTOR (FILTER INTERFACE) */

.selector {
    width: 800px;
    float: left;
    display: flex;
}

.selector select {
    width: 380px;
    height: 17.2em;
    flex: 1 0 auto;
}

.selector-available, .selector-chosen {
    width: 380px;
    text-align: center;
    margin-bottom: 5px;
    display: flex;
    flex-direction: column;
}

.selector-available h2, .selector-chosen h2 {
    border: 1px solid var(--border-color);
    border-radius: 4px 4px 0 0;
}

.selector-chosen .list-footer-display {
    border: 1px solid var(--border-color);
    border-top: none;
    border-radius: 0 0 4px 4px;
    margin: 0 0 10px;
    padding: 8px;
    text-align: center;
    background: var(--primary);
    color: var(--header-link-color);
    cursor: pointer;
}
.selector-chosen .list-footer-display__clear {
    color: var(--breadcrumbs-fg);
}

.selector-chosen h2 {
    background: var(--primary);
    color: var(--header-link-color);
}

.selector .selector-available h2 {
    background: var(--darkened-bg);
    color: var(--body-quiet-color);
}

.selector .selector-filter {
    border: 1px solid var(--border-color);
    border-width: 0 1px;
    padding: 8px;
    color: var(--body-quiet-color);
    font-size: 0.625rem;
    margin: 0;
    text-align: left;
}

.selector .selector-filter label,
.inline-group .aligned .selector .selector-filter label {
    float: left;
    margin: 7px 0 0;
    width: 18px;
    height: 18px;
    padding: 0;
    overflow: hidden;
    line-height: 1;
    min-width: auto;
}

.selector .selector-available input,
.selector .selector-chosen input {
    width: 320px;
    margin-left: 8px;
}

.selector ul.selector-chooser {
    align-self: center;
    width: 22px;
    background-color: var(--selected-bg);
    border-radius: 10px;
    margin: 0 5px;
    padding: 0;
    transform: translateY(-17px);
}

.selector-chooser li {
    margin: 0;
    padding: 3px;
    list-style-type: none;
}

.selector select {
    padding: 0 10px;
    margin: 0 0 10px;
    border-radius: 0 0 4px 4px;
}
.selector .selector-chosen--with-filtered select {
    margin: 0;
    border-radius: 0;
    height: 14em;
}

.selector .selector-chosen:not(.selector-chosen--with-filtered) .list-footer-display {
    display: none;
}

.selector-add, .selector-remove {
    width: 16px;
    height: 16px;
    display: block;
    text-indent: -3000px;
    overflow: hidden;
    cursor: default;
    opacity: 0.55;
}

.active.selector-add, .active.selector-remove {
    opacity: 1;
}

.active.selector-add:hover, .active.selector-remove:hover {
    cursor: pointer;
}

.selector-add {
    background: url(../img/selector-icons.svg) 0 -96px no-repeat;
}

.active.selector-add:focus, .active.selector-add:hover {
    background-position: 0 -112px;
}

.selector-remove {
    background: url(../img/selector-icons.svg) 0 -64px no-repeat;
}

.active.selector-remove:focus, .active.selector-remove:hover {
    background-position: 0 -80px;
}

a.selector-chooseall, a.selector-clearall {
    display: inline-block;
    height: 16px;
    text-align: left;
    margin: 1px auto 3px;
    overflow: hidden;
    font-weight: bold;
    line-height: 16px;
    color: var(--body-quiet-color);
    text-decoration: none;
    opacity: 0.55;
}

a.active.selector-chooseall:focus, a.active.selector-clearall:focus,
a.active.selector-chooseall:hover, a.active.selector-clearall:hover {
    color: var(--link-fg);
}

a.active.selector-chooseall, a.active.selector-clearall {
    opacity: 1;
}

a.active.selector-chooseall:hover, a.active.selector-clearall:hover {
    cursor: pointer;
}

a.selector-chooseall {
    padding: 0 18px 0 0;
    background: url(../img/selector-icons.svg) right -160px no-repeat;
    cursor: default;
}

a.active.selector-chooseall:focus, a.active.selector-chooseall:hover {
    background-position: 100% -176px;
}

a.selector-clearall {
    padding: 0 0 0 18px;
    background: url(../img/selector-icons.svg) 0 -128px no-repeat;
    cursor: default;
}

a.active.selector-clearall:focus, a.active.selector-clearall:hover {
    background-position: 0 -144px;
}

/* STACKED SELECTORS */

.stacked {
    float: left;
    width: 490px;
    display: block;
}

.stacked select {
    width: 480px;
    height: 10.1em;
}

.stacked .selector-available, .stacked .selector-chosen {
    width: 480px;
}

.stacked .selector-available {
    margin-bottom: 0;
}

.stacked .selector-available input {
    width: 422px;
}

.stacked ul.selector-chooser {
    height: 22px;
    width: 50px;
    margin: 0 0 10px 40%;
    background-color: #eee;
    border-radius: 10px;
    transform: none;
}

.stacked .selector-chooser li {
    float: left;
    padding: 3px 3px 3px 5px;
}

.stacked .selector-chooseall, .stacked .selector-clearall {
    display: none;
}

.stacked .selector-add {
    background: url(../img/selector-icons.svg) 0 -32px no-repeat;
    cursor: default;
}

.stacked .active.selector-add {
    background-position: 0 -32px;
    cursor: pointer;
}

.stacked .active.selector-add:focus, .stacked .active.selector-add:hover {
    background-position: 0 -48px;
    cursor: pointer;
}

.stacked .selector-remove {
    background: url(../img/selector-icons.svg) 0 0 no-repeat;
    cursor: default;
}

.stacked .active.selector-remove {
    background-position: 0 0px;
    cursor: pointer;
}

.stacked .active.selector-remove:focus, .stacked .active.selector-remove:hover {
    background-position: 0 -16px;
    cursor: pointer;
}

.selector .help-icon {
    background: url(../img/icon-unknown.svg) 0 0 no-repeat;
    display: inline-block;
    vertical-align: middle;
    margin: -2px 0 0 2px;
    width: 13px;
    height: 13px;
}

.selector .selector-chosen .help-icon {
    background: url(../img/icon-unknown-alt.svg) 0 0 no-repeat;
}

.selector .search-label-icon {
    background: url(../img/search.svg) 0 0 no-repeat;
    display: inline-block;
    height: 1.125rem;
    width: 1.125rem;
}

/* DATE AND TIME */

p.datetime {
    line-height: 20px;
    margin: 0;
    padding: 0;
    color: var(--body-quiet-color);
    font-weight: bold;
}

.datetime span {
    white-space: nowrap;
    font-weight: normal;
    font-size: 0.6875rem;
    color: var(--body-quiet-color);
}

.datetime input, .form-row .datetime input.vDateField, .form-row .datetime input.vTimeField {
    margin-left: 5px;
    margin-bottom: 4px;
}

table p.datetime {
    font-size: 0.6875rem;
    margin-left: 0;
    padding-left: 0;
}

.datetimeshortcuts .clock-icon, .datetimeshortcuts .date-icon {
    position: relative;
    display: inline-block;
    vertical-align: middle;
    height: 16px;
    width: 16px;
    overflow: hidden;
}

.datetimeshortcuts .clock-icon {
    background: url(../img/icon-clock.svg) 0 0 no-repeat;
}

.datetimeshortcuts a:focus .clock-icon,
.datetimeshortcuts a:hover .clock-icon {
    background-position: 0 -16px;
}

.datetimeshortcuts .date-icon {
    background: url(../img/icon-calendar.svg) 0 0 no-repeat;
    top: -1px;
}

.datetimeshortcuts a:focus .date-icon,
.datetimeshortcuts a:hover .date-icon {
    background-position: 0 -16px;
}

.timezonewarning {
    font-size: 0.6875rem;
    color: var(--body-quiet-color);
}

/* URL */

p.url {
    line-height: 20px;
    margin: 0;
    padding: 0;
    color: var(--body-quiet-color);
    font-size: 0.6875rem;
    font-weight: bold;
}

.url a {
    font-weight: normal;
}

/* FILE UPLOADS */

p.file-upload {
    line-height: 20px;
    margin: 0;
    padding: 0;
    color: var(--body-quiet-color);
    font-size: 0.6875rem;
    font-weight: bold;
}

.file-upload a {
    font-weight: normal;
}

.file-upload .deletelink {
    margin-left: 5px;
}

span.clearable-file-input label {
    color: var(--body-fg);
    font-size: 0.6875rem;
    display: inline;
    float: none;
}

/* CALENDARS & CLOCKS */

.calendarbox, .clockbox {
    margin: 5px auto;
    font-size: 0.75rem;
    width: 19em;
    text-align: center;
    background: var(--body-bg);
    color: var(--body-fg);
    border: 1px solid var(--hairline-color);
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    position: relative;
}

.clockbox {
    width: auto;
}

.calendar {
    margin: 0;
    padding: 0;
}

.calendar table {
    margin: 0;
    padding: 0;
    border-collapse: collapse;
    background: white;
    width: 100%;
}

.calendar caption, .calendarbox h2 {
    margin: 0;
    text-align: center;
    border-top: none;
    font-weight: 700;
    font-size: 0.75rem;
    color: #333;
    background: var(--accent);
}

.calendar th {
    padding: 8px 5px;
    background: var(--darkened-bg);
    border-bottom: 1px solid var(--border-color);
    font-weight: 400;
    font-size: 0.75rem;
    text-align: center;
    color: var(--body-quiet-color);
}

.calendar td {
    font-weight: 400;
    font-size: 0.75rem;
    text-align: center;
    padding: 0;
    border-top: 1px solid var(--hairline-color);
    border-bottom: none;
}

.calendar td.selected a {
    background: var(--primary);
    color: var(--button-fg);
}

.calendar td.nonday {
    background: var(--darkened-bg);
}

.calendar td.today a {
    font-weight: 700;
}

.calendar td a, .timelist a {
    display: block;
    font-weight: 400;
    padding: 6px;
    text-decoration: none;
    color: var(--body-quiet-color);
}

.calendar td a:focus, .timelist a:focus,
.calendar td a:hover, .timelist a:hover {
    background: var(--primary);
    color: white;
}

.calendar td a:active, .timelist a:active {
    background: var(--header-bg);
    color: white;
}

.calendarnav {
    font-size: 0.625rem;
    text-align: center;
    color: #ccc;
    margin: 0;
    padding: 1px 3px;
}

.calendarnav a:link, #calendarnav a:visited,
#calendarnav a:focus, #calendarnav a:hover {
    color: var(--body-quiet-color);
}

.calendar-shortcuts {
    background: var(--body-bg);
    color: var(--body-quiet-color);
    font-size: 0.6875rem;
    line-height: 0.6875rem;
    border-top: 1px solid var(--hairline-color);
    padding: 8px 0;
}

.calendarbox .calendarnav-previous, .calendarbox .calendarnav-next {
    display: block;
    position: absolute;
    top: 8px;
    width: 15px;
    height: 15px;
    text-indent: -9999px;
    padding: 0;
}

.calendarnav-previous {
    left: 10px;
    background: url(../img/calendar-icons.svg) 0 0 no-repeat;
}

.calendarbox .calendarnav-previous:focus,
.calendarbox .calendarnav-previous:hover {
    background-position: 0 -15px;
}

.calendarnav-next {
    right: 10px;
    background: url(../img/calendar-icons.svg) 0 -30px no-repeat;
}

.calendarbox .calendarnav-next:focus,
.calendarbox .calendarnav-next:hover {
    background-position: 0 -45px;
}

.calendar-cancel {
    margin: 0;
    padding: 4px 0;
    font-size: 0.75rem;
    background: #eee;
    border-top: 1px solid var(--border-color);
    color: var(--body-fg);
}

.calendar-cancel:focus, .calendar-cancel:hover {
    background: #ddd;
}

.calendar-cancel a {
    color: black;
    display: block;
}

ul.timelist, .timelist li {
    list-style-type: none;
    margin: 0;
    padding: 0;
}

.timelist a {
    padding: 2px;
}

/* EDIT INLINE */

.inline-deletelink {
    float: right;
    text-indent: -9999px;
    background: url(../img/inline-delete.svg) 0 0 no-repeat;
    width: 16px;
    height: 16px;
    border: 0px none;
}

.inline-deletelink:focus, .inline-deletelink:hover {
    cursor: pointer;
}

/* RELATED WIDGET WRAPPER */
.related-widget-wrapper {
    float: left;       /* display properly in form rows with multiple fields */
    overflow: hidden;  /* clear floated contents */
}

.related-widget-wrapper-link {
    opacity: 0.3;
}

.related-widget-wrapper-link:link {
    opacity: .8;
}

.related-widget-wrapper-link:link:focus,
.related-widget-wrapper-link:link:hover {
    opacity: 1;
}

select + .related-widget-wrapper-link,
.related-widget-wrapper-link + .related-widget-wrapper-link {
    margin-left: 7px;
}

/* GIS MAPS */
.dj_map {
    width: 600px;
    height: 400px;
}

```

# staticfiles/admin/img/calendar-icons.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/gis/move_vertex_off.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/gis/move_vertex_on.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-addlink.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-alert.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-calendar.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-changelink.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-clock.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-deletelink.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-no.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-unknown-alt.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-unknown.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-viewlink.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/icon-yes.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/inline-delete.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/LICENSE

```
The MIT License (MIT)

Copyright (c) 2014 Code Charm Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

```

# staticfiles/admin/img/README.txt

```txt
All icons are taken from Font Awesome (http://fontawesome.io/) project.
The Font Awesome font is licensed under the SIL OFL 1.1:
- https://scripts.sil.org/OFL

SVG icons source: https://github.com/encharm/Font-Awesome-SVG-PNG
Font-Awesome-SVG-PNG is licensed under the MIT license (see file license
in current folder).

```

# staticfiles/admin/img/search.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/selector-icons.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/sorting-icons.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/tooltag-add.svg

This is a file of the type: SVG Image

# staticfiles/admin/img/tooltag-arrowright.svg

This is a file of the type: SVG Image

# staticfiles/admin/js/actions.js

```js
/*global gettext, interpolate, ngettext*/
'use strict';
{
    function show(selector) {
        document.querySelectorAll(selector).forEach(function(el) {
            el.classList.remove('hidden');
        });
    }

    function hide(selector) {
        document.querySelectorAll(selector).forEach(function(el) {
            el.classList.add('hidden');
        });
    }

    function showQuestion(options) {
        hide(options.acrossClears);
        show(options.acrossQuestions);
        hide(options.allContainer);
    }

    function showClear(options) {
        show(options.acrossClears);
        hide(options.acrossQuestions);
        document.querySelector(options.actionContainer).classList.remove(options.selectedClass);
        show(options.allContainer);
        hide(options.counterContainer);
    }

    function reset(options) {
        hide(options.acrossClears);
        hide(options.acrossQuestions);
        hide(options.allContainer);
        show(options.counterContainer);
    }

    function clearAcross(options) {
        reset(options);
        const acrossInputs = document.querySelectorAll(options.acrossInput);
        acrossInputs.forEach(function(acrossInput) {
            acrossInput.value = 0;
        });
        document.querySelector(options.actionContainer).classList.remove(options.selectedClass);
    }

    function checker(actionCheckboxes, options, checked) {
        if (checked) {
            showQuestion(options);
        } else {
            reset(options);
        }
        actionCheckboxes.forEach(function(el) {
            el.checked = checked;
            el.closest('tr').classList.toggle(options.selectedClass, checked);
        });
    }

    function updateCounter(actionCheckboxes, options) {
        const sel = Array.from(actionCheckboxes).filter(function(el) {
            return el.checked;
        }).length;
        const counter = document.querySelector(options.counterContainer);
        // data-actions-icnt is defined in the generated HTML
        // and contains the total amount of objects in the queryset
        const actions_icnt = Number(counter.dataset.actionsIcnt);
        counter.textContent = interpolate(
            ngettext('%(sel)s of %(cnt)s selected', '%(sel)s of %(cnt)s selected', sel), {
                sel: sel,
                cnt: actions_icnt
            }, true);
        const allToggle = document.getElementById(options.allToggleId);
        allToggle.checked = sel === actionCheckboxes.length;
        if (allToggle.checked) {
            showQuestion(options);
        } else {
            clearAcross(options);
        }
    }

    const defaults = {
        actionContainer: "div.actions",
        counterContainer: "span.action-counter",
        allContainer: "div.actions span.all",
        acrossInput: "div.actions input.select-across",
        acrossQuestions: "div.actions span.question",
        acrossClears: "div.actions span.clear",
        allToggleId: "action-toggle",
        selectedClass: "selected"
    };

    window.Actions = function(actionCheckboxes, options) {
        options = Object.assign({}, defaults, options);
        let list_editable_changed = false;
        let lastChecked = null;
        let shiftPressed = false;

        document.addEventListener('keydown', (event) => {
            shiftPressed = event.shiftKey;
        });

        document.addEventListener('keyup', (event) => {
            shiftPressed = event.shiftKey;
        });

        document.getElementById(options.allToggleId).addEventListener('click', function(event) {
            checker(actionCheckboxes, options, this.checked);
            updateCounter(actionCheckboxes, options);
        });

        document.querySelectorAll(options.acrossQuestions + " a").forEach(function(el) {
            el.addEventListener('click', function(event) {
                event.preventDefault();
                const acrossInputs = document.querySelectorAll(options.acrossInput);
                acrossInputs.forEach(function(acrossInput) {
                    acrossInput.value = 1;
                });
                showClear(options);
            });
        });

        document.querySelectorAll(options.acrossClears + " a").forEach(function(el) {
            el.addEventListener('click', function(event) {
                event.preventDefault();
                document.getElementById(options.allToggleId).checked = false;
                clearAcross(options);
                checker(actionCheckboxes, options, false);
                updateCounter(actionCheckboxes, options);
            });
        });

        function affectedCheckboxes(target, withModifier) {
            const multiSelect = (lastChecked && withModifier && lastChecked !== target);
            if (!multiSelect) {
                return [target];
            }
            const checkboxes = Array.from(actionCheckboxes);
            const targetIndex = checkboxes.findIndex(el => el === target);
            const lastCheckedIndex = checkboxes.findIndex(el => el === lastChecked);
            const startIndex = Math.min(targetIndex, lastCheckedIndex);
            const endIndex = Math.max(targetIndex, lastCheckedIndex);
            const filtered = checkboxes.filter((el, index) => (startIndex <= index) && (index <= endIndex));
            return filtered;
        };

        Array.from(document.getElementById('result_list').tBodies).forEach(function(el) {
            el.addEventListener('change', function(event) {
                const target = event.target;
                if (target.classList.contains('action-select')) {
                    const checkboxes = affectedCheckboxes(target, shiftPressed);
                    checker(checkboxes, options, target.checked);
                    updateCounter(actionCheckboxes, options);
                    lastChecked = target;
                } else {
                    list_editable_changed = true;
                }
            });
        });

        document.querySelector('#changelist-form button[name=index]').addEventListener('click', function(event) {
            if (list_editable_changed) {
                const confirmed = confirm(gettext("You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost."));
                if (!confirmed) {
                    event.preventDefault();
                }
            }
        });

        const el = document.querySelector('#changelist-form input[name=_save]');
        // The button does not exist if no fields are editable.
        if (el) {
            el.addEventListener('click', function(event) {
                if (document.querySelector('[name=action]').value) {
                    const text = list_editable_changed
                        ? gettext("You have selected an action, but you haven’t saved your changes to individual fields yet. Please click OK to save. You’ll need to re-run the action.")
                        : gettext("You have selected an action, and you haven’t made any changes on individual fields. You’re probably looking for the Go button rather than the Save button.");
                    if (!confirm(text)) {
                        event.preventDefault();
                    }
                }
            });
        }
    };

    // Call function fn when the DOM is loaded and ready. If it is already
    // loaded, call the function now.
    // http://youmightnotneedjquery.com/#ready
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    ready(function() {
        const actionsEls = document.querySelectorAll('tr input.action-select');
        if (actionsEls.length > 0) {
            Actions(actionsEls);
        }
    });
}

```

# staticfiles/admin/js/admin/DateTimeShortcuts.js

```js
/*global Calendar, findPosX, findPosY, get_format, gettext, gettext_noop, interpolate, ngettext, quickElement*/
// Inserts shortcut buttons after all of the following:
//     <input type="text" class="vDateField">
//     <input type="text" class="vTimeField">
'use strict';
{
    const DateTimeShortcuts = {
        calendars: [],
        calendarInputs: [],
        clockInputs: [],
        clockHours: {
            default_: [
                [gettext_noop('Now'), -1],
                [gettext_noop('Midnight'), 0],
                [gettext_noop('6 a.m.'), 6],
                [gettext_noop('Noon'), 12],
                [gettext_noop('6 p.m.'), 18]
            ]
        },
        dismissClockFunc: [],
        dismissCalendarFunc: [],
        calendarDivName1: 'calendarbox', // name of calendar <div> that gets toggled
        calendarDivName2: 'calendarin', // name of <div> that contains calendar
        calendarLinkName: 'calendarlink', // name of the link that is used to toggle
        clockDivName: 'clockbox', // name of clock <div> that gets toggled
        clockLinkName: 'clocklink', // name of the link that is used to toggle
        shortCutsClass: 'datetimeshortcuts', // class of the clock and cal shortcuts
        timezoneWarningClass: 'timezonewarning', // class of the warning for timezone mismatch
        timezoneOffset: 0,
        init: function() {
            const serverOffset = document.body.dataset.adminUtcOffset;
            if (serverOffset) {
                const localOffset = new Date().getTimezoneOffset() * -60;
                DateTimeShortcuts.timezoneOffset = localOffset - serverOffset;
            }

            for (const inp of document.getElementsByTagName('input')) {
                if (inp.type === 'text' && inp.classList.contains('vTimeField')) {
                    DateTimeShortcuts.addClock(inp);
                    DateTimeShortcuts.addTimezoneWarning(inp);
                }
                else if (inp.type === 'text' && inp.classList.contains('vDateField')) {
                    DateTimeShortcuts.addCalendar(inp);
                    DateTimeShortcuts.addTimezoneWarning(inp);
                }
            }
        },
        // Return the current time while accounting for the server timezone.
        now: function() {
            const serverOffset = document.body.dataset.adminUtcOffset;
            if (serverOffset) {
                const localNow = new Date();
                const localOffset = localNow.getTimezoneOffset() * -60;
                localNow.setTime(localNow.getTime() + 1000 * (serverOffset - localOffset));
                return localNow;
            } else {
                return new Date();
            }
        },
        // Add a warning when the time zone in the browser and backend do not match.
        addTimezoneWarning: function(inp) {
            const warningClass = DateTimeShortcuts.timezoneWarningClass;
            let timezoneOffset = DateTimeShortcuts.timezoneOffset / 3600;

            // Only warn if there is a time zone mismatch.
            if (!timezoneOffset) {
                return;
            }

            // Check if warning is already there.
            if (inp.parentNode.querySelectorAll('.' + warningClass).length) {
                return;
            }

            let message;
            if (timezoneOffset > 0) {
                message = ngettext(
                    'Note: You are %s hour ahead of server time.',
                    'Note: You are %s hours ahead of server time.',
                    timezoneOffset
                );
            }
            else {
                timezoneOffset *= -1;
                message = ngettext(
                    'Note: You are %s hour behind server time.',
                    'Note: You are %s hours behind server time.',
                    timezoneOffset
                );
            }
            message = interpolate(message, [timezoneOffset]);

            const warning = document.createElement('div');
            warning.classList.add('help', warningClass);
            warning.textContent = message;
            inp.parentNode.appendChild(warning);
        },
        // Add clock widget to a given field
        addClock: function(inp) {
            const num = DateTimeShortcuts.clockInputs.length;
            DateTimeShortcuts.clockInputs[num] = inp;
            DateTimeShortcuts.dismissClockFunc[num] = function() { DateTimeShortcuts.dismissClock(num); return true; };

            // Shortcut links (clock icon and "Now" link)
            const shortcuts_span = document.createElement('span');
            shortcuts_span.className = DateTimeShortcuts.shortCutsClass;
            inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);
            const now_link = document.createElement('a');
            now_link.href = "#";
            now_link.textContent = gettext('Now');
            now_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.handleClockQuicklink(num, -1);
            });
            const clock_link = document.createElement('a');
            clock_link.href = '#';
            clock_link.id = DateTimeShortcuts.clockLinkName + num;
            clock_link.addEventListener('click', function(e) {
                e.preventDefault();
                // avoid triggering the document click handler to dismiss the clock
                e.stopPropagation();
                DateTimeShortcuts.openClock(num);
            });

            quickElement(
                'span', clock_link, '',
                'class', 'clock-icon',
                'title', gettext('Choose a Time')
            );
            shortcuts_span.appendChild(document.createTextNode('\u00A0'));
            shortcuts_span.appendChild(now_link);
            shortcuts_span.appendChild(document.createTextNode('\u00A0|\u00A0'));
            shortcuts_span.appendChild(clock_link);

            // Create clock link div
            //
            // Markup looks like:
            // <div id="clockbox1" class="clockbox module">
            //     <h2>Choose a time</h2>
            //     <ul class="timelist">
            //         <li><a href="#">Now</a></li>
            //         <li><a href="#">Midnight</a></li>
            //         <li><a href="#">6 a.m.</a></li>
            //         <li><a href="#">Noon</a></li>
            //         <li><a href="#">6 p.m.</a></li>
            //     </ul>
            //     <p class="calendar-cancel"><a href="#">Cancel</a></p>
            // </div>

            const clock_box = document.createElement('div');
            clock_box.style.display = 'none';
            clock_box.style.position = 'absolute';
            clock_box.className = 'clockbox module';
            clock_box.id = DateTimeShortcuts.clockDivName + num;
            document.body.appendChild(clock_box);
            clock_box.addEventListener('click', function(e) { e.stopPropagation(); });

            quickElement('h2', clock_box, gettext('Choose a time'));
            const time_list = quickElement('ul', clock_box);
            time_list.className = 'timelist';
            // The list of choices can be overridden in JavaScript like this:
            // DateTimeShortcuts.clockHours.name = [['3 a.m.', 3]];
            // where name is the name attribute of the <input>.
            const name = typeof DateTimeShortcuts.clockHours[inp.name] === 'undefined' ? 'default_' : inp.name;
            DateTimeShortcuts.clockHours[name].forEach(function(element) {
                const time_link = quickElement('a', quickElement('li', time_list), gettext(element[0]), 'href', '#');
                time_link.addEventListener('click', function(e) {
                    e.preventDefault();
                    DateTimeShortcuts.handleClockQuicklink(num, element[1]);
                });
            });

            const cancel_p = quickElement('p', clock_box);
            cancel_p.className = 'calendar-cancel';
            const cancel_link = quickElement('a', cancel_p, gettext('Cancel'), 'href', '#');
            cancel_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.dismissClock(num);
            });

            document.addEventListener('keyup', function(event) {
                if (event.which === 27) {
                    // ESC key closes popup
                    DateTimeShortcuts.dismissClock(num);
                    event.preventDefault();
                }
            });
        },
        openClock: function(num) {
            const clock_box = document.getElementById(DateTimeShortcuts.clockDivName + num);
            const clock_link = document.getElementById(DateTimeShortcuts.clockLinkName + num);

            // Recalculate the clockbox position
            // is it left-to-right or right-to-left layout ?
            if (window.getComputedStyle(document.body).direction !== 'rtl') {
                clock_box.style.left = findPosX(clock_link) + 17 + 'px';
            }
            else {
                // since style's width is in em, it'd be tough to calculate
                // px value of it. let's use an estimated px for now
                clock_box.style.left = findPosX(clock_link) - 110 + 'px';
            }
            clock_box.style.top = Math.max(0, findPosY(clock_link) - 30) + 'px';

            // Show the clock box
            clock_box.style.display = 'block';
            document.addEventListener('click', DateTimeShortcuts.dismissClockFunc[num]);
        },
        dismissClock: function(num) {
            document.getElementById(DateTimeShortcuts.clockDivName + num).style.display = 'none';
            document.removeEventListener('click', DateTimeShortcuts.dismissClockFunc[num]);
        },
        handleClockQuicklink: function(num, val) {
            let d;
            if (val === -1) {
                d = DateTimeShortcuts.now();
            }
            else {
                d = new Date(1970, 1, 1, val, 0, 0, 0);
            }
            DateTimeShortcuts.clockInputs[num].value = d.strftime(get_format('TIME_INPUT_FORMATS')[0]);
            DateTimeShortcuts.clockInputs[num].focus();
            DateTimeShortcuts.dismissClock(num);
        },
        // Add calendar widget to a given field.
        addCalendar: function(inp) {
            const num = DateTimeShortcuts.calendars.length;

            DateTimeShortcuts.calendarInputs[num] = inp;
            DateTimeShortcuts.dismissCalendarFunc[num] = function() { DateTimeShortcuts.dismissCalendar(num); return true; };

            // Shortcut links (calendar icon and "Today" link)
            const shortcuts_span = document.createElement('span');
            shortcuts_span.className = DateTimeShortcuts.shortCutsClass;
            inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);
            const today_link = document.createElement('a');
            today_link.href = '#';
            today_link.appendChild(document.createTextNode(gettext('Today')));
            today_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.handleCalendarQuickLink(num, 0);
            });
            const cal_link = document.createElement('a');
            cal_link.href = '#';
            cal_link.id = DateTimeShortcuts.calendarLinkName + num;
            cal_link.addEventListener('click', function(e) {
                e.preventDefault();
                // avoid triggering the document click handler to dismiss the calendar
                e.stopPropagation();
                DateTimeShortcuts.openCalendar(num);
            });
            quickElement(
                'span', cal_link, '',
                'class', 'date-icon',
                'title', gettext('Choose a Date')
            );
            shortcuts_span.appendChild(document.createTextNode('\u00A0'));
            shortcuts_span.appendChild(today_link);
            shortcuts_span.appendChild(document.createTextNode('\u00A0|\u00A0'));
            shortcuts_span.appendChild(cal_link);

            // Create calendarbox div.
            //
            // Markup looks like:
            //
            // <div id="calendarbox3" class="calendarbox module">
            //     <h2>
            //           <a href="#" class="link-previous">&lsaquo;</a>
            //           <a href="#" class="link-next">&rsaquo;</a> February 2003
            //     </h2>
            //     <div class="calendar" id="calendarin3">
            //         <!-- (cal) -->
            //     </div>
            //     <div class="calendar-shortcuts">
            //          <a href="#">Yesterday</a> | <a href="#">Today</a> | <a href="#">Tomorrow</a>
            //     </div>
            //     <p class="calendar-cancel"><a href="#">Cancel</a></p>
            // </div>
            const cal_box = document.createElement('div');
            cal_box.style.display = 'none';
            cal_box.style.position = 'absolute';
            cal_box.className = 'calendarbox module';
            cal_box.id = DateTimeShortcuts.calendarDivName1 + num;
            document.body.appendChild(cal_box);
            cal_box.addEventListener('click', function(e) { e.stopPropagation(); });

            // next-prev links
            const cal_nav = quickElement('div', cal_box);
            const cal_nav_prev = quickElement('a', cal_nav, '<', 'href', '#');
            cal_nav_prev.className = 'calendarnav-previous';
            cal_nav_prev.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.drawPrev(num);
            });

            const cal_nav_next = quickElement('a', cal_nav, '>', 'href', '#');
            cal_nav_next.className = 'calendarnav-next';
            cal_nav_next.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.drawNext(num);
            });

            // main box
            const cal_main = quickElement('div', cal_box, '', 'id', DateTimeShortcuts.calendarDivName2 + num);
            cal_main.className = 'calendar';
            DateTimeShortcuts.calendars[num] = new Calendar(DateTimeShortcuts.calendarDivName2 + num, DateTimeShortcuts.handleCalendarCallback(num));
            DateTimeShortcuts.calendars[num].drawCurrent();

            // calendar shortcuts
            const shortcuts = quickElement('div', cal_box);
            shortcuts.className = 'calendar-shortcuts';
            let day_link = quickElement('a', shortcuts, gettext('Yesterday'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.handleCalendarQuickLink(num, -1);
            });
            shortcuts.appendChild(document.createTextNode('\u00A0|\u00A0'));
            day_link = quickElement('a', shortcuts, gettext('Today'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.handleCalendarQuickLink(num, 0);
            });
            shortcuts.appendChild(document.createTextNode('\u00A0|\u00A0'));
            day_link = quickElement('a', shortcuts, gettext('Tomorrow'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.handleCalendarQuickLink(num, +1);
            });

            // cancel bar
            const cancel_p = quickElement('p', cal_box);
            cancel_p.className = 'calendar-cancel';
            const cancel_link = quickElement('a', cancel_p, gettext('Cancel'), 'href', '#');
            cancel_link.addEventListener('click', function(e) {
                e.preventDefault();
                DateTimeShortcuts.dismissCalendar(num);
            });
            document.addEventListener('keyup', function(event) {
                if (event.which === 27) {
                    // ESC key closes popup
                    DateTimeShortcuts.dismissCalendar(num);
                    event.preventDefault();
                }
            });
        },
        openCalendar: function(num) {
            const cal_box = document.getElementById(DateTimeShortcuts.calendarDivName1 + num);
            const cal_link = document.getElementById(DateTimeShortcuts.calendarLinkName + num);
            const inp = DateTimeShortcuts.calendarInputs[num];

            // Determine if the current value in the input has a valid date.
            // If so, draw the calendar with that date's year and month.
            if (inp.value) {
                const format = get_format('DATE_INPUT_FORMATS')[0];
                const selected = inp.value.strptime(format);
                const year = selected.getUTCFullYear();
                const month = selected.getUTCMonth() + 1;
                const re = /\d{4}/;
                if (re.test(year.toString()) && month >= 1 && month <= 12) {
                    DateTimeShortcuts.calendars[num].drawDate(month, year, selected);
                }
            }

            // Recalculate the clockbox position
            // is it left-to-right or right-to-left layout ?
            if (window.getComputedStyle(document.body).direction !== 'rtl') {
                cal_box.style.left = findPosX(cal_link) + 17 + 'px';
            }
            else {
                // since style's width is in em, it'd be tough to calculate
                // px value of it. let's use an estimated px for now
                cal_box.style.left = findPosX(cal_link) - 180 + 'px';
            }
            cal_box.style.top = Math.max(0, findPosY(cal_link) - 75) + 'px';

            cal_box.style.display = 'block';
            document.addEventListener('click', DateTimeShortcuts.dismissCalendarFunc[num]);
        },
        dismissCalendar: function(num) {
            document.getElementById(DateTimeShortcuts.calendarDivName1 + num).style.display = 'none';
            document.removeEventListener('click', DateTimeShortcuts.dismissCalendarFunc[num]);
        },
        drawPrev: function(num) {
            DateTimeShortcuts.calendars[num].drawPreviousMonth();
        },
        drawNext: function(num) {
            DateTimeShortcuts.calendars[num].drawNextMonth();
        },
        handleCalendarCallback: function(num) {
            const format = get_format('DATE_INPUT_FORMATS')[0];
            return function(y, m, d) {
                DateTimeShortcuts.calendarInputs[num].value = new Date(y, m - 1, d).strftime(format);
                DateTimeShortcuts.calendarInputs[num].focus();
                document.getElementById(DateTimeShortcuts.calendarDivName1 + num).style.display = 'none';
            };
        },
        handleCalendarQuickLink: function(num, offset) {
            const d = DateTimeShortcuts.now();
            d.setDate(d.getDate() + offset);
            DateTimeShortcuts.calendarInputs[num].value = d.strftime(get_format('DATE_INPUT_FORMATS')[0]);
            DateTimeShortcuts.calendarInputs[num].focus();
            DateTimeShortcuts.dismissCalendar(num);
        }
    };

    window.addEventListener('load', DateTimeShortcuts.init);
    window.DateTimeShortcuts = DateTimeShortcuts;
}

```

# staticfiles/admin/js/admin/RelatedObjectLookups.js

```js
/*global SelectBox, interpolate*/
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
'use strict';
{
    const $ = django.jQuery;
    let popupIndex = 0;
    const relatedWindows = [];

    function dismissChildPopups() {
        relatedWindows.forEach(function(win) {
            if(!win.closed) {
                win.dismissChildPopups();
                win.close();    
            }
        });
    }

    function setPopupIndex() {
        if(document.getElementsByName("_popup").length > 0) {
            const index = window.name.lastIndexOf("__") + 2;
            popupIndex = parseInt(window.name.substring(index));   
        } else {
            popupIndex = 0;
        }
    }

    function addPopupIndex(name) {
        return name + "__" + (popupIndex + 1);
    }

    function removePopupIndex(name) {
        return name.replace(new RegExp("__" + (popupIndex + 1) + "$"), '');
    }

    function showAdminPopup(triggeringLink, name_regexp, add_popup) {
        const name = addPopupIndex(triggeringLink.id.replace(name_regexp, ''));
        const href = new URL(triggeringLink.href);
        if (add_popup) {
            href.searchParams.set('_popup', 1);
        }
        const win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        relatedWindows.push(win);
        win.focus();
        return false;
    }

    function showRelatedObjectLookupPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^lookup_/, true);
    }

    function dismissRelatedLookupPopup(win, chosenId) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
            elem.value += ',' + chosenId;
        } else {
            document.getElementById(name).value = chosenId;
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function showRelatedObjectPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
    }

    function updateRelatedObjectLinks(triggeringLink) {
        const $this = $(triggeringLink);
        const siblings = $this.nextAll('.view-related, .change-related, .delete-related');
        if (!siblings.length) {
            return;
        }
        const value = $this.val();
        if (value) {
            siblings.each(function() {
                const elm = $(this);
                elm.attr('href', elm.attr('data-href-template').replace('__fk__', value));
            });
        } else {
            siblings.removeAttr('href');
        }
    }

    function updateRelatedSelectsOptions(currentSelect, win, objId, newRepr, newId) {
        // After create/edit a model from the options next to the current
        // select (+ or :pencil:) update ForeignKey PK of the rest of selects
        // in the page.

        const path = win.location.pathname;
        // Extract the model from the popup url '.../<model>/add/' or
        // '.../<model>/<id>/change/' depending the action (add or change).
        const modelName = path.split('/')[path.split('/').length - (objId ? 4 : 3)];
        // Exclude autocomplete selects.
        const selectsRelated = document.querySelectorAll(`[data-model-ref="${modelName}"] select:not(.admin-autocomplete)`);

        selectsRelated.forEach(function(select) {
            if (currentSelect === select) {
                return;
            }

            let option = select.querySelector(`option[value="${objId}"]`);

            if (!option) {
                option = new Option(newRepr, newId);
                select.options.add(option);
                return;
            }

            option.textContent = newRepr;
            option.value = newId;
        });
    }

    function dismissAddRelatedObjectPopup(win, newId, newRepr) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem) {
            const elemName = elem.nodeName.toUpperCase();
            if (elemName === 'SELECT') {
                elem.options[elem.options.length] = new Option(newRepr, newId, true, true);
                updateRelatedSelectsOptions(elem, win, null, newRepr, newId);
            } else if (elemName === 'INPUT') {
                if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
                    elem.value += ',' + newId;
                } else {
                    elem.value = newId;
                }
            }
            // Trigger a change event to update related links if required.
            $(elem).trigger('change');
        } else {
            const toId = name + "_to";
            const o = new Option(newRepr, newId);
            SelectBox.add_to_cache(toId, o);
            SelectBox.redisplay(toId);
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissChangeRelatedObjectPopup(win, objId, newRepr, newId) {
        const id = removePopupIndex(win.name.replace(/^edit_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                this.textContent = newRepr;
                this.value = newId;
            }
        }).trigger('change');
        updateRelatedSelectsOptions(selects[0], win, objId, newRepr, newId);
        selects.next().find('.select2-selection__rendered').each(function() {
            // The element can have a clear button as a child.
            // Use the lastChild to modify only the displayed value.
            this.lastChild.textContent = newRepr;
            this.title = newRepr;
        });
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissDeleteRelatedObjectPopup(win, objId) {
        const id = removePopupIndex(win.name.replace(/^delete_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                $(this).remove();
            }
        }).trigger('change');
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    window.showRelatedObjectLookupPopup = showRelatedObjectLookupPopup;
    window.dismissRelatedLookupPopup = dismissRelatedLookupPopup;
    window.showRelatedObjectPopup = showRelatedObjectPopup;
    window.updateRelatedObjectLinks = updateRelatedObjectLinks;
    window.dismissAddRelatedObjectPopup = dismissAddRelatedObjectPopup;
    window.dismissChangeRelatedObjectPopup = dismissChangeRelatedObjectPopup;
    window.dismissDeleteRelatedObjectPopup = dismissDeleteRelatedObjectPopup;
    window.dismissChildPopups = dismissChildPopups;

    // Kept for backward compatibility
    window.showAddAnotherPopup = showRelatedObjectPopup;
    window.dismissAddAnotherPopup = dismissAddRelatedObjectPopup;

    window.addEventListener('unload', function(evt) {
        window.dismissChildPopups();
    });

    $(document).ready(function() {
        setPopupIndex();
        $("a[data-popup-opener]").on('click', function(event) {
            event.preventDefault();
            opener.dismissRelatedLookupPopup(window, $(this).data("popup-opener"));
        });
        $('body').on('click', '.related-widget-wrapper-link[data-popup="yes"]', function(e) {
            e.preventDefault();
            if (this.href) {
                const event = $.Event('django:show-related', {href: this.href});
                $(this).trigger(event);
                if (!event.isDefaultPrevented()) {
                    showRelatedObjectPopup(this);
                }
            }
        });
        $('body').on('change', '.related-widget-wrapper select', function(e) {
            const event = $.Event('django:update-related');
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                updateRelatedObjectLinks(this);
            }
        });
        $('.related-widget-wrapper select').trigger('change');
        $('body').on('click', '.related-lookup', function(e) {
            e.preventDefault();
            const event = $.Event('django:lookup-related');
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                showRelatedObjectLookupPopup(this);
            }
        });
    });
}

```

# staticfiles/admin/js/autocomplete.js

```js
'use strict';
{
    const $ = django.jQuery;

    $.fn.djangoAdminSelect2 = function() {
        $.each(this, function(i, element) {
            $(element).select2({
                ajax: {
                    data: (params) => {
                        return {
                            term: params.term,
                            page: params.page,
                            app_label: element.dataset.appLabel,
                            model_name: element.dataset.modelName,
                            field_name: element.dataset.fieldName
                        };
                    }
                }
            });
        });
        return this;
    };

    $(function() {
        // Initialize all autocomplete widgets except the one in the template
        // form used when a new formset is added.
        $('.admin-autocomplete').not('[name*=__prefix__]').djangoAdminSelect2();
    });

    document.addEventListener('formset:added', (event) => {
        $(event.target).find('.admin-autocomplete').djangoAdminSelect2();
    });
}

```

# staticfiles/admin/js/calendar.js

```js
/*global gettext, pgettext, get_format, quickElement, removeChildren*/
/*
calendar.js - Calendar functions by Adrian Holovaty
depends on core.js for utility functions like removeChildren or quickElement
*/
'use strict';
{
    // CalendarNamespace -- Provides a collection of HTML calendar-related helper functions
    const CalendarNamespace = {
        monthsOfYear: [
            gettext('January'),
            gettext('February'),
            gettext('March'),
            gettext('April'),
            gettext('May'),
            gettext('June'),
            gettext('July'),
            gettext('August'),
            gettext('September'),
            gettext('October'),
            gettext('November'),
            gettext('December')
        ],
        monthsOfYearAbbrev: [
            pgettext('abbrev. month January', 'Jan'),
            pgettext('abbrev. month February', 'Feb'),
            pgettext('abbrev. month March', 'Mar'),
            pgettext('abbrev. month April', 'Apr'),
            pgettext('abbrev. month May', 'May'),
            pgettext('abbrev. month June', 'Jun'),
            pgettext('abbrev. month July', 'Jul'),
            pgettext('abbrev. month August', 'Aug'),
            pgettext('abbrev. month September', 'Sep'),
            pgettext('abbrev. month October', 'Oct'),
            pgettext('abbrev. month November', 'Nov'),
            pgettext('abbrev. month December', 'Dec')
        ],
        daysOfWeek: [
            pgettext('one letter Sunday', 'S'),
            pgettext('one letter Monday', 'M'),
            pgettext('one letter Tuesday', 'T'),
            pgettext('one letter Wednesday', 'W'),
            pgettext('one letter Thursday', 'T'),
            pgettext('one letter Friday', 'F'),
            pgettext('one letter Saturday', 'S')
        ],
        firstDayOfWeek: parseInt(get_format('FIRST_DAY_OF_WEEK')),
        isLeapYear: function(year) {
            return (((year % 4) === 0) && ((year % 100) !== 0 ) || ((year % 400) === 0));
        },
        getDaysInMonth: function(month, year) {
            let days;
            if (month === 1 || month === 3 || month === 5 || month === 7 || month === 8 || month === 10 || month === 12) {
                days = 31;
            }
            else if (month === 4 || month === 6 || month === 9 || month === 11) {
                days = 30;
            }
            else if (month === 2 && CalendarNamespace.isLeapYear(year)) {
                days = 29;
            }
            else {
                days = 28;
            }
            return days;
        },
        draw: function(month, year, div_id, callback, selected) { // month = 1-12, year = 1-9999
            const today = new Date();
            const todayDay = today.getDate();
            const todayMonth = today.getMonth() + 1;
            const todayYear = today.getFullYear();
            let todayClass = '';

            // Use UTC functions here because the date field does not contain time
            // and using the UTC function variants prevent the local time offset
            // from altering the date, specifically the day field.  For example:
            //
            // \`\`\`
            // var x = new Date('2013-10-02');
            // var day = x.getDate();
            // \`\`\`
            //
            // The day variable above will be 1 instead of 2 in, say, US Pacific time
            // zone.
            let isSelectedMonth = false;
            if (typeof selected !== 'undefined') {
                isSelectedMonth = (selected.getUTCFullYear() === year && (selected.getUTCMonth() + 1) === month);
            }

            month = parseInt(month);
            year = parseInt(year);
            const calDiv = document.getElementById(div_id);
            removeChildren(calDiv);
            const calTable = document.createElement('table');
            quickElement('caption', calTable, CalendarNamespace.monthsOfYear[month - 1] + ' ' + year);
            const tableBody = quickElement('tbody', calTable);

            // Draw days-of-week header
            let tableRow = quickElement('tr', tableBody);
            for (let i = 0; i < 7; i++) {
                quickElement('th', tableRow, CalendarNamespace.daysOfWeek[(i + CalendarNamespace.firstDayOfWeek) % 7]);
            }

            const startingPos = new Date(year, month - 1, 1 - CalendarNamespace.firstDayOfWeek).getDay();
            const days = CalendarNamespace.getDaysInMonth(month, year);

            let nonDayCell;

            // Draw blanks before first of month
            tableRow = quickElement('tr', tableBody);
            for (let i = 0; i < startingPos; i++) {
                nonDayCell = quickElement('td', tableRow, ' ');
                nonDayCell.className = "nonday";
            }

            function calendarMonth(y, m) {
                function onClick(e) {
                    e.preventDefault();
                    callback(y, m, this.textContent);
                }
                return onClick;
            }

            // Draw days of month
            let currentDay = 1;
            for (let i = startingPos; currentDay <= days; i++) {
                if (i % 7 === 0 && currentDay !== 1) {
                    tableRow = quickElement('tr', tableBody);
                }
                if ((currentDay === todayDay) && (month === todayMonth) && (year === todayYear)) {
                    todayClass = 'today';
                } else {
                    todayClass = '';
                }

                // use UTC function; see above for explanation.
                if (isSelectedMonth && currentDay === selected.getUTCDate()) {
                    if (todayClass !== '') {
                        todayClass += " ";
                    }
                    todayClass += "selected";
                }

                const cell = quickElement('td', tableRow, '', 'class', todayClass);
                const link = quickElement('a', cell, currentDay, 'href', '#');
                link.addEventListener('click', calendarMonth(year, month));
                currentDay++;
            }

            // Draw blanks after end of month (optional, but makes for valid code)
            while (tableRow.childNodes.length < 7) {
                nonDayCell = quickElement('td', tableRow, ' ');
                nonDayCell.className = "nonday";
            }

            calDiv.appendChild(calTable);
        }
    };

    // Calendar -- A calendar instance
    function Calendar(div_id, callback, selected) {
        // div_id (string) is the ID of the element in which the calendar will
        //     be displayed
        // callback (string) is the name of a JavaScript function that will be
        //     called with the parameters (year, month, day) when a day in the
        //     calendar is clicked
        this.div_id = div_id;
        this.callback = callback;
        this.today = new Date();
        this.currentMonth = this.today.getMonth() + 1;
        this.currentYear = this.today.getFullYear();
        if (typeof selected !== 'undefined') {
            this.selected = selected;
        }
    }
    Calendar.prototype = {
        drawCurrent: function() {
            CalendarNamespace.draw(this.currentMonth, this.currentYear, this.div_id, this.callback, this.selected);
        },
        drawDate: function(month, year, selected) {
            this.currentMonth = month;
            this.currentYear = year;

            if(selected) {
                this.selected = selected;
            }

            this.drawCurrent();
        },
        drawPreviousMonth: function() {
            if (this.currentMonth === 1) {
                this.currentMonth = 12;
                this.currentYear--;
            }
            else {
                this.currentMonth--;
            }
            this.drawCurrent();
        },
        drawNextMonth: function() {
            if (this.currentMonth === 12) {
                this.currentMonth = 1;
                this.currentYear++;
            }
            else {
                this.currentMonth++;
            }
            this.drawCurrent();
        },
        drawPreviousYear: function() {
            this.currentYear--;
            this.drawCurrent();
        },
        drawNextYear: function() {
            this.currentYear++;
            this.drawCurrent();
        }
    };
    window.Calendar = Calendar;
    window.CalendarNamespace = CalendarNamespace;
}

```

# staticfiles/admin/js/cancel.js

```js
'use strict';
{
    // Call function fn when the DOM is loaded and ready. If it is already
    // loaded, call the function now.
    // http://youmightnotneedjquery.com/#ready
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    ready(function() {
        function handleClick(event) {
            event.preventDefault();
            const params = new URLSearchParams(window.location.search);
            if (params.has('_popup')) {
                window.close(); // Close the popup.
            } else {
                window.history.back(); // Otherwise, go back.
            }
        }

        document.querySelectorAll('.cancel-link').forEach(function(el) {
            el.addEventListener('click', handleClick);
        });
    });
}

```

# staticfiles/admin/js/change_form.js

```js
'use strict';
{
    const inputTags = ['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
    const modelName = document.getElementById('django-admin-form-add-constants').dataset.modelName;
    if (modelName) {
        const form = document.getElementById(modelName + '_form');
        for (const element of form.elements) {
            // HTMLElement.offsetParent returns null when the element is not
            // rendered.
            if (inputTags.includes(element.tagName) && !element.disabled && element.offsetParent) {
                element.focus();
                break;
            }
        }
    }
}

```

# staticfiles/admin/js/collapse.js

```js
/*global gettext*/
'use strict';
{
    window.addEventListener('load', function() {
        // Add anchor tag for Show/Hide link
        const fieldsets = document.querySelectorAll('fieldset.collapse');
        for (const [i, elem] of fieldsets.entries()) {
            // Don't hide if fields in this fieldset have errors
            if (elem.querySelectorAll('div.errors, ul.errorlist').length === 0) {
                elem.classList.add('collapsed');
                const h2 = elem.querySelector('h2');
                const link = document.createElement('a');
                link.id = 'fieldsetcollapser' + i;
                link.className = 'collapse-toggle';
                link.href = '#';
                link.textContent = gettext('Show');
                h2.appendChild(document.createTextNode(' ('));
                h2.appendChild(link);
                h2.appendChild(document.createTextNode(')'));
            }
        }
        // Add toggle to hide/show anchor tag
        const toggleFunc = function(ev) {
            if (ev.target.matches('.collapse-toggle')) {
                ev.preventDefault();
                ev.stopPropagation();
                const fieldset = ev.target.closest('fieldset');
                if (fieldset.classList.contains('collapsed')) {
                    // Show
                    ev.target.textContent = gettext('Hide');
                    fieldset.classList.remove('collapsed');
                } else {
                    // Hide
                    ev.target.textContent = gettext('Show');
                    fieldset.classList.add('collapsed');
                }
            }
        };
        document.querySelectorAll('fieldset.module').forEach(function(el) {
            el.addEventListener('click', toggleFunc);
        });
    });
}

```

# staticfiles/admin/js/core.js

```js
// Core JavaScript helper functions
'use strict';

// quickElement(tagType, parentReference [, textInChildNode, attribute, attributeValue ...]);
function quickElement() {
    const obj = document.createElement(arguments[0]);
    if (arguments[2]) {
        const textNode = document.createTextNode(arguments[2]);
        obj.appendChild(textNode);
    }
    const len = arguments.length;
    for (let i = 3; i < len; i += 2) {
        obj.setAttribute(arguments[i], arguments[i + 1]);
    }
    arguments[1].appendChild(obj);
    return obj;
}

// "a" is reference to an object
function removeChildren(a) {
    while (a.hasChildNodes()) {
        a.removeChild(a.lastChild);
    }
}

// ----------------------------------------------------------------------------
// Find-position functions by PPK
// See https://www.quirksmode.org/js/findpos.html
// ----------------------------------------------------------------------------
function findPosX(obj) {
    let curleft = 0;
    if (obj.offsetParent) {
        while (obj.offsetParent) {
            curleft += obj.offsetLeft - obj.scrollLeft;
            obj = obj.offsetParent;
        }
    } else if (obj.x) {
        curleft += obj.x;
    }
    return curleft;
}

function findPosY(obj) {
    let curtop = 0;
    if (obj.offsetParent) {
        while (obj.offsetParent) {
            curtop += obj.offsetTop - obj.scrollTop;
            obj = obj.offsetParent;
        }
    } else if (obj.y) {
        curtop += obj.y;
    }
    return curtop;
}

//-----------------------------------------------------------------------------
// Date object extensions
// ----------------------------------------------------------------------------
{
    Date.prototype.getTwelveHours = function() {
        return this.getHours() % 12 || 12;
    };

    Date.prototype.getTwoDigitMonth = function() {
        return (this.getMonth() < 9) ? '0' + (this.getMonth() + 1) : (this.getMonth() + 1);
    };

    Date.prototype.getTwoDigitDate = function() {
        return (this.getDate() < 10) ? '0' + this.getDate() : this.getDate();
    };

    Date.prototype.getTwoDigitTwelveHour = function() {
        return (this.getTwelveHours() < 10) ? '0' + this.getTwelveHours() : this.getTwelveHours();
    };

    Date.prototype.getTwoDigitHour = function() {
        return (this.getHours() < 10) ? '0' + this.getHours() : this.getHours();
    };

    Date.prototype.getTwoDigitMinute = function() {
        return (this.getMinutes() < 10) ? '0' + this.getMinutes() : this.getMinutes();
    };

    Date.prototype.getTwoDigitSecond = function() {
        return (this.getSeconds() < 10) ? '0' + this.getSeconds() : this.getSeconds();
    };

    Date.prototype.getAbbrevMonthName = function() {
        return typeof window.CalendarNamespace === "undefined"
            ? this.getTwoDigitMonth()
            : window.CalendarNamespace.monthsOfYearAbbrev[this.getMonth()];
    };

    Date.prototype.getFullMonthName = function() {
        return typeof window.CalendarNamespace === "undefined"
            ? this.getTwoDigitMonth()
            : window.CalendarNamespace.monthsOfYear[this.getMonth()];
    };

    Date.prototype.strftime = function(format) {
        const fields = {
            b: this.getAbbrevMonthName(),
            B: this.getFullMonthName(),
            c: this.toString(),
            d: this.getTwoDigitDate(),
            H: this.getTwoDigitHour(),
            I: this.getTwoDigitTwelveHour(),
            m: this.getTwoDigitMonth(),
            M: this.getTwoDigitMinute(),
            p: (this.getHours() >= 12) ? 'PM' : 'AM',
            S: this.getTwoDigitSecond(),
            w: '0' + this.getDay(),
            x: this.toLocaleDateString(),
            X: this.toLocaleTimeString(),
            y: ('' + this.getFullYear()).substr(2, 4),
            Y: '' + this.getFullYear(),
            '%': '%'
        };
        let result = '', i = 0;
        while (i < format.length) {
            if (format.charAt(i) === '%') {
                result += fields[format.charAt(i + 1)];
                ++i;
            }
            else {
                result += format.charAt(i);
            }
            ++i;
        }
        return result;
    };

    // ----------------------------------------------------------------------------
    // String object extensions
    // ----------------------------------------------------------------------------
    String.prototype.strptime = function(format) {
        const split_format = format.split(/[.\-/]/);
        const date = this.split(/[.\-/]/);
        let i = 0;
        let day, month, year;
        while (i < split_format.length) {
            switch (split_format[i]) {
            case "%d":
                day = date[i];
                break;
            case "%m":
                month = date[i] - 1;
                break;
            case "%Y":
                year = date[i];
                break;
            case "%y":
                // A %y value in the range of [00, 68] is in the current
                // century, while [69, 99] is in the previous century,
                // according to the Open Group Specification.
                if (parseInt(date[i], 10) >= 69) {
                    year = date[i];
                } else {
                    year = (new Date(Date.UTC(date[i], 0))).getUTCFullYear() + 100;
                }
                break;
            }
            ++i;
        }
        // Create Date object from UTC since the parsed value is supposed to be
        // in UTC, not local time. Also, the calendar uses UTC functions for
        // date extraction.
        return new Date(Date.UTC(year, month, day));
    };
}

```

# staticfiles/admin/js/filters.js

```js
/**
 * Persist changelist filters state (collapsed/expanded).
 */
'use strict';
{
    // Init filters.
    let filters = JSON.parse(sessionStorage.getItem('django.admin.filtersState'));

    if (!filters) {
        filters = {};
    }

    Object.entries(filters).forEach(([key, value]) => {
        const detailElement = document.querySelector(`[data-filter-title='${CSS.escape(key)}']`);

        // Check if the filter is present, it could be from other view.
        if (detailElement) {
            value ? detailElement.setAttribute('open', '') : detailElement.removeAttribute('open');
        }
    });

    // Save filter state when clicks.
    const details = document.querySelectorAll('details');
    details.forEach(detail => {
        detail.addEventListener('toggle', event => {
            filters[`${event.target.dataset.filterTitle}`] = detail.open;
            sessionStorage.setItem('django.admin.filtersState', JSON.stringify(filters));
        });
    });
}

```

# staticfiles/admin/js/inlines.js

```js
/*global DateTimeShortcuts, SelectFilter*/
/**
 * Django admin inlines
 *
 * Based on jQuery Formset 1.1
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Spiced up with Code from Zain Memon's GSoC project 2009
 * and modified for Django by Jannis Leidel, Travis Swicegood and Julien Phalip.
 *
 * Licensed under the New BSD License
 * See: https://opensource.org/licenses/bsd-license.php
 */
'use strict';
{
    const $ = django.jQuery;
    $.fn.formset = function(opts) {
        const options = $.extend({}, $.fn.formset.defaults, opts);
        const $this = $(this);
        const $parent = $this.parent();
        const updateElementIndex = function(el, prefix, ndx) {
            const id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
            const replacement = prefix + "-" + ndx;
            if ($(el).prop("for")) {
                $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
            }
            if (el.id) {
                el.id = el.id.replace(id_regex, replacement);
            }
            if (el.name) {
                el.name = el.name.replace(id_regex, replacement);
            }
        };
        const totalForms = $("#id_" + options.prefix + "-TOTAL_FORMS").prop("autocomplete", "off");
        let nextIndex = parseInt(totalForms.val(), 10);
        const maxForms = $("#id_" + options.prefix + "-MAX_NUM_FORMS").prop("autocomplete", "off");
        const minForms = $("#id_" + options.prefix + "-MIN_NUM_FORMS").prop("autocomplete", "off");
        let addButton;

        /**
         * The "Add another MyModel" button below the inline forms.
         */
        const addInlineAddButton = function() {
            if (addButton === null) {
                if ($this.prop("tagName") === "TR") {
                    // If forms are laid out as table rows, insert the
                    // "add" button in a new table row:
                    const numCols = $this.eq(-1).children().length;
                    $parent.append('<tr class="' + options.addCssClass + '"><td colspan="' + numCols + '"><a href="#">' + options.addText + "</a></tr>");
                    addButton = $parent.find("tr:last a");
                } else {
                    // Otherwise, insert it immediately after the last form:
                    $this.filter(":last").after('<div class="' + options.addCssClass + '"><a href="#">' + options.addText + "</a></div>");
                    addButton = $this.filter(":last").next().find("a");
                }
            }
            addButton.on('click', addInlineClickHandler);
        };

        const addInlineClickHandler = function(e) {
            e.preventDefault();
            const template = $("#" + options.prefix + "-empty");
            const row = template.clone(true);
            row.removeClass(options.emptyCssClass)
                .addClass(options.formCssClass)
                .attr("id", options.prefix + "-" + nextIndex);
            addInlineDeleteButton(row);
            row.find("*").each(function() {
                updateElementIndex(this, options.prefix, totalForms.val());
            });
            // Insert the new form when it has been fully edited.
            row.insertBefore($(template));
            // Update number of total forms.
            $(totalForms).val(parseInt(totalForms.val(), 10) + 1);
            nextIndex += 1;
            // Hide the add button if there's a limit and it's been reached.
            if ((maxForms.val() !== '') && (maxForms.val() - totalForms.val()) <= 0) {
                addButton.parent().hide();
            }
            // Show the remove buttons if there are more than min_num.
            toggleDeleteButtonVisibility(row.closest('.inline-group'));

            // Pass the new form to the post-add callback, if provided.
            if (options.added) {
                options.added(row);
            }
            row.get(0).dispatchEvent(new CustomEvent("formset:added", {
                bubbles: true,
                detail: {
                    formsetName: options.prefix
                }
            }));
        };

        /**
         * The "X" button that is part of every unsaved inline.
         * (When saved, it is replaced with a "Delete" checkbox.)
         */
        const addInlineDeleteButton = function(row) {
            if (row.is("tr")) {
                // If the forms are laid out in table rows, insert
                // the remove button into the last table cell:
                row.children(":last").append('<div><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></div>");
            } else if (row.is("ul") || row.is("ol")) {
                // If they're laid out as an ordered/unordered list,
                // insert an <li> after the last list item:
                row.append('<li><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></li>");
            } else {
                // Otherwise, just insert the remove button as the
                // last child element of the form's container:
                row.children(":first").append('<span><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></span>");
            }
            // Add delete handler for each row.
            row.find("a." + options.deleteCssClass).on('click', inlineDeleteHandler.bind(this));
        };

        const inlineDeleteHandler = function(e1) {
            e1.preventDefault();
            const deleteButton = $(e1.target);
            const row = deleteButton.closest('.' + options.formCssClass);
            const inlineGroup = row.closest('.inline-group');
            // Remove the parent form containing this button,
            // and also remove the relevant row with non-field errors:
            const prevRow = row.prev();
            if (prevRow.length && prevRow.hasClass('row-form-errors')) {
                prevRow.remove();
            }
            row.remove();
            nextIndex -= 1;
            // Pass the deleted form to the post-delete callback, if provided.
            if (options.removed) {
                options.removed(row);
            }
            document.dispatchEvent(new CustomEvent("formset:removed", {
                detail: {
                    formsetName: options.prefix
                }
            }));
            // Update the TOTAL_FORMS form count.
            const forms = $("." + options.formCssClass);
            $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
            // Show add button again once below maximum number.
            if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                addButton.parent().show();
            }
            // Hide the remove buttons if at min_num.
            toggleDeleteButtonVisibility(inlineGroup);
            // Also, update names and ids for all remaining form controls so
            // they remain in sequence:
            let i, formCount;
            const updateElementCallback = function() {
                updateElementIndex(this, options.prefix, i);
            };
            for (i = 0, formCount = forms.length; i < formCount; i++) {
                updateElementIndex($(forms).get(i), options.prefix, i);
                $(forms.get(i)).find("*").each(updateElementCallback);
            }
        };

        const toggleDeleteButtonVisibility = function(inlineGroup) {
            if ((minForms.val() !== '') && (minForms.val() - totalForms.val()) >= 0) {
                inlineGroup.find('.inline-deletelink').hide();
            } else {
                inlineGroup.find('.inline-deletelink').show();
            }
        };

        $this.each(function(i) {
            $(this).not("." + options.emptyCssClass).addClass(options.formCssClass);
        });

        // Create the delete buttons for all unsaved inlines:
        $this.filter('.' + options.formCssClass + ':not(.has_original):not(.' + options.emptyCssClass + ')').each(function() {
            addInlineDeleteButton($(this));
        });
        toggleDeleteButtonVisibility($this);

        // Create the add button, initially hidden.
        addButton = options.addButton;
        addInlineAddButton();

        // Show the add button if allowed to add more items.
        // Note that max_num = None translates to a blank string.
        const showAddButton = maxForms.val() === '' || (maxForms.val() - totalForms.val()) > 0;
        if ($this.length && showAddButton) {
            addButton.parent().show();
        } else {
            addButton.parent().hide();
        }

        return this;
    };

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        prefix: "form", // The form prefix for your django formset
        addText: "add another", // Text for the add link
        deleteText: "remove", // Text for the delete link
        addCssClass: "add-row", // CSS class applied to the add link
        deleteCssClass: "delete-row", // CSS class applied to the delete link
        emptyCssClass: "empty-row", // CSS class applied to the empty row
        formCssClass: "dynamic-form", // CSS class applied to each form in a formset
        added: null, // Function called each time a new form is added
        removed: null, // Function called each time a form is deleted
        addButton: null // Existing add button to use
    };


    // Tabular inlines ---------------------------------------------------------
    $.fn.tabularFormset = function(selector, options) {
        const $rows = $(this);

        const reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force
            if (typeof DateTimeShortcuts !== "undefined") {
                $(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        const updateSelectFilter = function() {
            // If any SelectFilter widgets are a part of the new form,
            // instantiate a new SelectFilter instance for it.
            if (typeof SelectFilter !== 'undefined') {
                $('.selectfilter').each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, false);
                });
                $('.selectfilterstacked').each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, true);
                });
            }
        };

        const initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                const field = $(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                $.each(dependency_list, function(i, field_name) {
                    dependencies.push('#' + row.find('.field-' + field_name).find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        $rows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
            },
            addButton: options.addButton
        });

        return $rows;
    };

    // Stacked inlines ---------------------------------------------------------
    $.fn.stackedFormset = function(selector, options) {
        const $rows = $(this);
        const updateInlineLabel = function(row) {
            $(selector).find(".inline_label").each(function(i) {
                const count = i + 1;
                $(this).html($(this).html().replace(/(#\d+)/g, "#" + count));
            });
        };

        const reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force, yuck.
            if (typeof DateTimeShortcuts !== "undefined") {
                $(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        const updateSelectFilter = function() {
            // If any SelectFilter widgets were added, instantiate a new instance.
            if (typeof SelectFilter !== "undefined") {
                $(".selectfilter").each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, false);
                });
                $(".selectfilterstacked").each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, true);
                });
            }
        };

        const initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                const field = $(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                $.each(dependency_list, function(i, field_name) {
                    // Dependency in a fieldset.
                    let field_element = row.find('.form-row .field-' + field_name);
                    // Dependency without a fieldset.
                    if (!field_element.length) {
                        field_element = row.find('.form-row.field-' + field_name);
                    }
                    dependencies.push('#' + field_element.find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        $rows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: updateInlineLabel,
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
                updateInlineLabel(row);
            },
            addButton: options.addButton
        });

        return $rows;
    };

    $(document).ready(function() {
        $(".js-inline-admin-formset").each(function() {
            const data = $(this).data(),
                inlineOptions = data.inlineFormset;
            let selector;
            switch(data.inlineType) {
            case "stacked":
                selector = inlineOptions.name + "-group .inline-related";
                $(selector).stackedFormset(selector, inlineOptions.options);
                break;
            case "tabular":
                selector = inlineOptions.name + "-group .tabular.inline-related tbody:first > tr.form-row";
                $(selector).tabularFormset(selector, inlineOptions.options);
                break;
            }
        });
    });
}

```

# staticfiles/admin/js/jquery.init.js

```js
/*global jQuery:false*/
'use strict';
/* Puts the included jQuery into our own namespace using noConflict and passing
 * it 'true'. This ensures that the included jQuery doesn't pollute the global
 * namespace (i.e. this preserves pre-existing values for both window.$ and
 * window.jQuery).
 */
window.django = {jQuery: jQuery.noConflict(true)};

```

# staticfiles/admin/js/nav_sidebar.js

```js
'use strict';
{
    const toggleNavSidebar = document.getElementById('toggle-nav-sidebar');
    if (toggleNavSidebar !== null) {
        const navSidebar = document.getElementById('nav-sidebar');
        const main = document.getElementById('main');
        let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');
        if (navSidebarIsOpen === null) {
            navSidebarIsOpen = 'true';
        }
        main.classList.toggle('shifted', navSidebarIsOpen === 'true');
        navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);

        toggleNavSidebar.addEventListener('click', function() {
            if (navSidebarIsOpen === 'true') {
                navSidebarIsOpen = 'false';
            } else {
                navSidebarIsOpen = 'true';
            }
            localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
            main.classList.toggle('shifted');
            navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
        });
    }

    function initSidebarQuickFilter() {
        const options = [];
        const navSidebar = document.getElementById('nav-sidebar');
        if (!navSidebar) {
            return;
        }
        navSidebar.querySelectorAll('th[scope=row] a').forEach((container) => {
            options.push({title: container.innerHTML, node: container});
        });

        function checkValue(event) {
            let filterValue = event.target.value;
            if (filterValue) {
                filterValue = filterValue.toLowerCase();
            }
            if (event.key === 'Escape') {
                filterValue = '';
                event.target.value = ''; // clear input
            }
            let matches = false;
            for (const o of options) {
                let displayValue = '';
                if (filterValue) {
                    if (o.title.toLowerCase().indexOf(filterValue) === -1) {
                        displayValue = 'none';
                    } else {
                        matches = true;
                    }
                }
                // show/hide parent <TR>
                o.node.parentNode.parentNode.style.display = displayValue;
            }
            if (!filterValue || matches) {
                event.target.classList.remove('no-results');
            } else {
                event.target.classList.add('no-results');
            }
            sessionStorage.setItem('django.admin.navSidebarFilterValue', filterValue);
        }

        const nav = document.getElementById('nav-filter');
        nav.addEventListener('change', checkValue, false);
        nav.addEventListener('input', checkValue, false);
        nav.addEventListener('keyup', checkValue, false);

        const storedValue = sessionStorage.getItem('django.admin.navSidebarFilterValue');
        if (storedValue) {
            nav.value = storedValue;
            checkValue({target: nav, key: ''});
        }
    }
    window.initSidebarQuickFilter = initSidebarQuickFilter;
    initSidebarQuickFilter();
}

```

# staticfiles/admin/js/popup_response.js

```js
/*global opener */
'use strict';
{
    const initData = JSON.parse(document.getElementById('django-admin-popup-response-constants').dataset.popupResponse);
    switch(initData.action) {
    case 'change':
        opener.dismissChangeRelatedObjectPopup(window, initData.value, initData.obj, initData.new_value);
        break;
    case 'delete':
        opener.dismissDeleteRelatedObjectPopup(window, initData.value);
        break;
    default:
        opener.dismissAddRelatedObjectPopup(window, initData.value, initData.obj);
        break;
    }
}

```

# staticfiles/admin/js/prepopulate_init.js

```js
'use strict';
{
    const $ = django.jQuery;
    const fields = $('#django-admin-prepopulated-fields-constants').data('prepopulatedFields');
    $.each(fields, function(index, field) {
        $(
            '.empty-form .form-row .field-' + field.name +
            ', .empty-form.form-row .field-' + field.name +
            ', .empty-form .form-row.field-' + field.name
        ).addClass('prepopulated_field');
        $(field.id).data('dependency_list', field.dependency_list).prepopulate(
            field.dependency_ids, field.maxLength, field.allowUnicode
        );
    });
}

```

# staticfiles/admin/js/prepopulate.js

```js
/*global URLify*/
'use strict';
{
    const $ = django.jQuery;
    $.fn.prepopulate = function(dependencies, maxLength, allowUnicode) {
        /*
            Depends on urlify.js
            Populates a selected field with the values of the dependent fields,
            URLifies and shortens the string.
            dependencies - array of dependent fields ids
            maxLength - maximum length of the URLify'd string
            allowUnicode - Unicode support of the URLify'd string
        */
        return this.each(function() {
            const prepopulatedField = $(this);

            const populate = function() {
                // Bail if the field's value has been changed by the user
                if (prepopulatedField.data('_changed')) {
                    return;
                }

                const values = [];
                $.each(dependencies, function(i, field) {
                    field = $(field);
                    if (field.val().length > 0) {
                        values.push(field.val());
                    }
                });
                prepopulatedField.val(URLify(values.join(' '), maxLength, allowUnicode));
            };

            prepopulatedField.data('_changed', false);
            prepopulatedField.on('change', function() {
                prepopulatedField.data('_changed', true);
            });

            if (!prepopulatedField.val()) {
                $(dependencies.join(',')).on('keyup change focus', populate);
            }
        });
    };
}

```

# staticfiles/admin/js/SelectBox.js

```js
'use strict';
{
    const SelectBox = {
        cache: {},
        init: function(id) {
            const box = document.getElementById(id);
            SelectBox.cache[id] = [];
            const cache = SelectBox.cache[id];
            for (const node of box.options) {
                cache.push({value: node.value, text: node.text, displayed: 1});
            }
        },
        redisplay: function(id) {
            // Repopulate HTML select box from cache
            const box = document.getElementById(id);
            const scroll_value_from_top = box.scrollTop;
            box.innerHTML = '';
            for (const node of SelectBox.cache[id]) {
                if (node.displayed) {
                    const new_option = new Option(node.text, node.value, false, false);
                    // Shows a tooltip when hovering over the option
                    new_option.title = node.text;
                    box.appendChild(new_option);
                }
            }
            box.scrollTop = scroll_value_from_top;
        },
        filter: function(id, text) {
            // Redisplay the HTML select box, displaying only the choices containing ALL
            // the words in text. (It's an AND search.)
            const tokens = text.toLowerCase().split(/\s+/);
            for (const node of SelectBox.cache[id]) {
                node.displayed = 1;
                const node_text = node.text.toLowerCase();
                for (const token of tokens) {
                    if (!node_text.includes(token)) {
                        node.displayed = 0;
                        break; // Once the first token isn't found we're done
                    }
                }
            }
            SelectBox.redisplay(id);
        },
        get_hidden_node_count(id) {
            const cache = SelectBox.cache[id] || [];
            return cache.filter(node => node.displayed === 0).length;
        },
        delete_from_cache: function(id, value) {
            let delete_index = null;
            const cache = SelectBox.cache[id];
            for (const [i, node] of cache.entries()) {
                if (node.value === value) {
                    delete_index = i;
                    break;
                }
            }
            cache.splice(delete_index, 1);
        },
        add_to_cache: function(id, option) {
            SelectBox.cache[id].push({value: option.value, text: option.text, displayed: 1});
        },
        cache_contains: function(id, value) {
            // Check if an item is contained in the cache
            for (const node of SelectBox.cache[id]) {
                if (node.value === value) {
                    return true;
                }
            }
            return false;
        },
        move: function(from, to) {
            const from_box = document.getElementById(from);
            for (const option of from_box.options) {
                const option_value = option.value;
                if (option.selected && SelectBox.cache_contains(from, option_value)) {
                    SelectBox.add_to_cache(to, {value: option_value, text: option.text, displayed: 1});
                    SelectBox.delete_from_cache(from, option_value);
                }
            }
            SelectBox.redisplay(from);
            SelectBox.redisplay(to);
        },
        move_all: function(from, to) {
            const from_box = document.getElementById(from);
            for (const option of from_box.options) {
                const option_value = option.value;
                if (SelectBox.cache_contains(from, option_value)) {
                    SelectBox.add_to_cache(to, {value: option_value, text: option.text, displayed: 1});
                    SelectBox.delete_from_cache(from, option_value);
                }
            }
            SelectBox.redisplay(from);
            SelectBox.redisplay(to);
        },
        sort: function(id) {
            SelectBox.cache[id].sort(function(a, b) {
                a = a.text.toLowerCase();
                b = b.text.toLowerCase();
                if (a > b) {
                    return 1;
                }
                if (a < b) {
                    return -1;
                }
                return 0;
            } );
        },
        select_all: function(id) {
            const box = document.getElementById(id);
            for (const option of box.options) {
                option.selected = true;
            }
        }
    };
    window.SelectBox = SelectBox;
}

```

# staticfiles/admin/js/SelectFilter2.js

```js
/*global SelectBox, gettext, interpolate, quickElement, SelectFilter*/
/*
SelectFilter2 - Turns a multiple-select box into a filter interface.

Requires core.js and SelectBox.js.
*/
'use strict';
{
    window.SelectFilter = {
        init: function(field_id, field_name, is_stacked) {
            if (field_id.match(/__prefix__/)) {
                // Don't initialize on empty forms.
                return;
            }
            const from_box = document.getElementById(field_id);
            from_box.id += '_from'; // change its ID
            from_box.className = 'filtered';

            for (const p of from_box.parentNode.getElementsByTagName('p')) {
                if (p.classList.contains("info")) {
                    // Remove <p class="info">, because it just gets in the way.
                    from_box.parentNode.removeChild(p);
                } else if (p.classList.contains("help")) {
                    // Move help text up to the top so it isn't below the select
                    // boxes or wrapped off on the side to the right of the add
                    // button:
                    from_box.parentNode.insertBefore(p, from_box.parentNode.firstChild);
                }
            }

            // <div class="selector"> or <div class="selector stacked">
            const selector_div = quickElement('div', from_box.parentNode);
            selector_div.className = is_stacked ? 'selector stacked' : 'selector';

            // <div class="selector-available">
            const selector_available = quickElement('div', selector_div);
            selector_available.className = 'selector-available';
            const title_available = quickElement('h2', selector_available, interpolate(gettext('Available %s') + ' ', [field_name]));
            quickElement(
                'span', title_available, '',
                'class', 'help help-tooltip help-icon',
                'title', interpolate(
                    gettext(
                        'This is the list of available %s. You may choose some by ' +
                        'selecting them in the box below and then clicking the ' +
                        '"Choose" arrow between the two boxes.'
                    ),
                    [field_name]
                )
            );

            const filter_p = quickElement('p', selector_available, '', 'id', field_id + '_filter');
            filter_p.className = 'selector-filter';

            const search_filter_label = quickElement('label', filter_p, '', 'for', field_id + '_input');

            quickElement(
                'span', search_filter_label, '',
                'class', 'help-tooltip search-label-icon',
                'title', interpolate(gettext("Type into this box to filter down the list of available %s."), [field_name])
            );

            filter_p.appendChild(document.createTextNode(' '));

            const filter_input = quickElement('input', filter_p, '', 'type', 'text', 'placeholder', gettext("Filter"));
            filter_input.id = field_id + '_input';

            selector_available.appendChild(from_box);
            const choose_all = quickElement('a', selector_available, gettext('Choose all'), 'title', interpolate(gettext('Click to choose all %s at once.'), [field_name]), 'href', '#', 'id', field_id + '_add_all_link');
            choose_all.className = 'selector-chooseall';

            // <ul class="selector-chooser">
            const selector_chooser = quickElement('ul', selector_div);
            selector_chooser.className = 'selector-chooser';
            const add_link = quickElement('a', quickElement('li', selector_chooser), gettext('Choose'), 'title', gettext('Choose'), 'href', '#', 'id', field_id + '_add_link');
            add_link.className = 'selector-add';
            const remove_link = quickElement('a', quickElement('li', selector_chooser), gettext('Remove'), 'title', gettext('Remove'), 'href', '#', 'id', field_id + '_remove_link');
            remove_link.className = 'selector-remove';

            // <div class="selector-chosen">
            const selector_chosen = quickElement('div', selector_div, '', 'id', field_id + '_selector_chosen');
            selector_chosen.className = 'selector-chosen';
            const title_chosen = quickElement('h2', selector_chosen, interpolate(gettext('Chosen %s') + ' ', [field_name]));
            quickElement(
                'span', title_chosen, '',
                'class', 'help help-tooltip help-icon',
                'title', interpolate(
                    gettext(
                        'This is the list of chosen %s. You may remove some by ' +
                        'selecting them in the box below and then clicking the ' +
                        '"Remove" arrow between the two boxes.'
                    ),
                    [field_name]
                )
            );
            
            const filter_selected_p = quickElement('p', selector_chosen, '', 'id', field_id + '_filter_selected');
            filter_selected_p.className = 'selector-filter';

            const search_filter_selected_label = quickElement('label', filter_selected_p, '', 'for', field_id + '_selected_input');

            quickElement(
                'span', search_filter_selected_label, '',
                'class', 'help-tooltip search-label-icon',
                'title', interpolate(gettext("Type into this box to filter down the list of selected %s."), [field_name])
            );

            filter_selected_p.appendChild(document.createTextNode(' '));

            const filter_selected_input = quickElement('input', filter_selected_p, '', 'type', 'text', 'placeholder', gettext("Filter"));
            filter_selected_input.id = field_id + '_selected_input';

            const to_box = quickElement('select', selector_chosen, '', 'id', field_id + '_to', 'multiple', '', 'size', from_box.size, 'name', from_box.name);
            to_box.className = 'filtered';
            
            const warning_footer = quickElement('div', selector_chosen, '', 'class', 'list-footer-display');
            quickElement('span', warning_footer, '', 'id', field_id + '_list-footer-display-text');
            quickElement('span', warning_footer, ' (click to clear)', 'class', 'list-footer-display__clear');
            
            const clear_all = quickElement('a', selector_chosen, gettext('Remove all'), 'title', interpolate(gettext('Click to remove all chosen %s at once.'), [field_name]), 'href', '#', 'id', field_id + '_remove_all_link');
            clear_all.className = 'selector-clearall';

            from_box.name = from_box.name + '_old';

            // Set up the JavaScript event handlers for the select box filter interface
            const move_selection = function(e, elem, move_func, from, to) {
                if (elem.classList.contains('active')) {
                    move_func(from, to);
                    SelectFilter.refresh_icons(field_id);
                    SelectFilter.refresh_filtered_selects(field_id);
                    SelectFilter.refresh_filtered_warning(field_id);
                }
                e.preventDefault();
            };
            choose_all.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move_all, field_id + '_from', field_id + '_to');
            });
            add_link.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move, field_id + '_from', field_id + '_to');
            });
            remove_link.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move, field_id + '_to', field_id + '_from');
            });
            clear_all.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move_all, field_id + '_to', field_id + '_from');
            });
            warning_footer.addEventListener('click', function(e) {
                filter_selected_input.value = '';
                SelectBox.filter(field_id + '_to', '');
                SelectFilter.refresh_filtered_warning(field_id);
                SelectFilter.refresh_icons(field_id);
            });
            filter_input.addEventListener('keypress', function(e) {
                SelectFilter.filter_key_press(e, field_id, '_from', '_to');
            });
            filter_input.addEventListener('keyup', function(e) {
                SelectFilter.filter_key_up(e, field_id, '_from');
            });
            filter_input.addEventListener('keydown', function(e) {
                SelectFilter.filter_key_down(e, field_id, '_from', '_to');
            });
            filter_selected_input.addEventListener('keypress', function(e) {
                SelectFilter.filter_key_press(e, field_id, '_to', '_from');
            });
            filter_selected_input.addEventListener('keyup', function(e) {
                SelectFilter.filter_key_up(e, field_id, '_to', '_selected_input');
            });
            filter_selected_input.addEventListener('keydown', function(e) {
                SelectFilter.filter_key_down(e, field_id, '_to', '_from');
            });
            selector_div.addEventListener('change', function(e) {
                if (e.target.tagName === 'SELECT') {
                    SelectFilter.refresh_icons(field_id);
                }
            });
            selector_div.addEventListener('dblclick', function(e) {
                if (e.target.tagName === 'OPTION') {
                    if (e.target.closest('select').id === field_id + '_to') {
                        SelectBox.move(field_id + '_to', field_id + '_from');
                    } else {
                        SelectBox.move(field_id + '_from', field_id + '_to');
                    }
                    SelectFilter.refresh_icons(field_id);
                }
            });
            from_box.closest('form').addEventListener('submit', function() {
                SelectBox.filter(field_id + '_to', '');
                SelectBox.select_all(field_id + '_to');
            });
            SelectBox.init(field_id + '_from');
            SelectBox.init(field_id + '_to');
            // Move selected from_box options to to_box
            SelectBox.move(field_id + '_from', field_id + '_to');

            // Initial icon refresh
            SelectFilter.refresh_icons(field_id);
        },
        any_selected: function(field) {
            // Temporarily add the required attribute and check validity.
            field.required = true;
            const any_selected = field.checkValidity();
            field.required = false;
            return any_selected;
        },
        refresh_filtered_warning: function(field_id) {
            const count = SelectBox.get_hidden_node_count(field_id + '_to');
            const selector = document.getElementById(field_id + '_selector_chosen');
            const warning = document.getElementById(field_id + '_list-footer-display-text');
            selector.className = selector.className.replace('selector-chosen--with-filtered', '');
            warning.textContent = interpolate(ngettext(
                '%s selected option not visible',
                '%s selected options not visible',
                count
            ), [count]);
            if(count > 0) {
                selector.className += ' selector-chosen--with-filtered';
            }
        },
        refresh_filtered_selects: function(field_id) {
            SelectBox.filter(field_id + '_from', document.getElementById(field_id + "_input").value);
            SelectBox.filter(field_id + '_to', document.getElementById(field_id + "_selected_input").value);
        },
        refresh_icons: function(field_id) {
            const from = document.getElementById(field_id + '_from');
            const to = document.getElementById(field_id + '_to');
            // Active if at least one item is selected
            document.getElementById(field_id + '_add_link').classList.toggle('active', SelectFilter.any_selected(from));
            document.getElementById(field_id + '_remove_link').classList.toggle('active', SelectFilter.any_selected(to));
            // Active if the corresponding box isn't empty
            document.getElementById(field_id + '_add_all_link').classList.toggle('active', from.querySelector('option'));
            document.getElementById(field_id + '_remove_all_link').classList.toggle('active', to.querySelector('option'));
            SelectFilter.refresh_filtered_warning(field_id);
        },
        filter_key_press: function(event, field_id, source, target) {
            const source_box = document.getElementById(field_id + source);
            // don't submit form if user pressed Enter
            if ((event.which && event.which === 13) || (event.keyCode && event.keyCode === 13)) {
                source_box.selectedIndex = 0;
                SelectBox.move(field_id + source, field_id + target);
                source_box.selectedIndex = 0;
                event.preventDefault();
            }
        },
        filter_key_up: function(event, field_id, source, filter_input) {
            const input = filter_input || '_input';
            const source_box = document.getElementById(field_id + source);
            const temp = source_box.selectedIndex;
            SelectBox.filter(field_id + source, document.getElementById(field_id + input).value);
            source_box.selectedIndex = temp;
            SelectFilter.refresh_filtered_warning(field_id);
            SelectFilter.refresh_icons(field_id);
        },
        filter_key_down: function(event, field_id, source, target) {
            const source_box = document.getElementById(field_id + source);
            // right key (39) or left key (37)
            const direction = source === '_from' ? 39 : 37;
            // right arrow -- move across
            if ((event.which && event.which === direction) || (event.keyCode && event.keyCode === direction)) {
                const old_index = source_box.selectedIndex;
                SelectBox.move(field_id + source, field_id + target);
                SelectFilter.refresh_filtered_selects(field_id);
                SelectFilter.refresh_filtered_warning(field_id);
                source_box.selectedIndex = (old_index === source_box.length) ? source_box.length - 1 : old_index;
                return;
            }
            // down arrow -- wrap around
            if ((event.which && event.which === 40) || (event.keyCode && event.keyCode === 40)) {
                source_box.selectedIndex = (source_box.length === source_box.selectedIndex + 1) ? 0 : source_box.selectedIndex + 1;
            }
            // up arrow -- wrap around
            if ((event.which && event.which === 38) || (event.keyCode && event.keyCode === 38)) {
                source_box.selectedIndex = (source_box.selectedIndex === 0) ? source_box.length - 1 : source_box.selectedIndex - 1;
            }
        }
    };

    window.addEventListener('load', function(e) {
        document.querySelectorAll('select.selectfilter, select.selectfilterstacked').forEach(function(el) {
            const data = el.dataset;
            SelectFilter.init(el.id, data.fieldName, parseInt(data.isStacked, 10));
        });
    });
}

```

# staticfiles/admin/js/theme.js

```js
'use strict';
{
    window.addEventListener('load', function(e) {

        function setTheme(mode) {
            if (mode !== "light" && mode !== "dark" && mode !== "auto") {
                console.error(`Got invalid theme mode: ${mode}. Resetting to auto.`);
                mode = "auto";
            }
            document.documentElement.dataset.theme = mode;
            localStorage.setItem("theme", mode);
        }

        function cycleTheme() {
            const currentTheme = localStorage.getItem("theme") || "auto";
            const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

            if (prefersDark) {
                // Auto (dark) -> Light -> Dark
                if (currentTheme === "auto") {
                    setTheme("light");
                } else if (currentTheme === "light") {
                    setTheme("dark");
                } else {
                    setTheme("auto");
                }
            } else {
                // Auto (light) -> Dark -> Light
                if (currentTheme === "auto") {
                    setTheme("dark");
                } else if (currentTheme === "dark") {
                    setTheme("light");
                } else {
                    setTheme("auto");
                }
            }
        }

        function initTheme() {
            // set theme defined in localStorage if there is one, or fallback to auto mode
            const currentTheme = localStorage.getItem("theme");
            currentTheme ? setTheme(currentTheme) : setTheme("auto");
        }

        function setupTheme() {
            // Attach event handlers for toggling themes
            const buttons = document.getElementsByClassName("theme-toggle");
            Array.from(buttons).forEach((btn) => {
                btn.addEventListener("click", cycleTheme);
            });
            initTheme();
        }

        setupTheme();
    });
}

```

# staticfiles/admin/js/urlify.js

```js
/*global XRegExp*/
'use strict';
{
    const LATIN_MAP = {
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Æ': 'AE',
        'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E', 'Ì': 'I', 'Í': 'I',
        'Î': 'I', 'Ï': 'I', 'Ð': 'D', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O',
        'Õ': 'O', 'Ö': 'O', 'Ő': 'O', 'Ø': 'O', 'Ù': 'U', 'Ú': 'U', 'Û': 'U',
        'Ü': 'U', 'Ű': 'U', 'Ý': 'Y', 'Þ': 'TH', 'Ÿ': 'Y', 'ß': 'ss', 'à': 'a',
        'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae', 'ç': 'c',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i',
        'ï': 'i', 'ð': 'd', 'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ö': 'o', 'ő': 'o', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ű': 'u', 'ý': 'y', 'þ': 'th', 'ÿ': 'y'
    };
    const LATIN_SYMBOLS_MAP = {
        '©': '(c)'
    };
    const GREEK_MAP = {
        'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h',
        'θ': '8', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': '3',
        'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'f',
        'χ': 'x', 'ψ': 'ps', 'ω': 'w', 'ά': 'a', 'έ': 'e', 'ί': 'i', 'ό': 'o',
        'ύ': 'y', 'ή': 'h', 'ώ': 'w', 'ς': 's', 'ϊ': 'i', 'ΰ': 'y', 'ϋ': 'y',
        'ΐ': 'i', 'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z',
        'Η': 'H', 'Θ': '8', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N',
        'Ξ': '3', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y',
        'Φ': 'F', 'Χ': 'X', 'Ψ': 'PS', 'Ω': 'W', 'Ά': 'A', 'Έ': 'E', 'Ί': 'I',
        'Ό': 'O', 'Ύ': 'Y', 'Ή': 'H', 'Ώ': 'W', 'Ϊ': 'I', 'Ϋ': 'Y'
    };
    const TURKISH_MAP = {
        'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ç': 'c', 'Ç': 'C', 'ü': 'u',
        'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ğ': 'g', 'Ğ': 'G'
    };
    const ROMANIAN_MAP = {
        'ă': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'â': 'a',
        'Ă': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T', 'Â': 'A'
    };
    const RUSSIAN_MAP = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': '',
        'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    };
    const UKRAINIAN_MAP = {
        'Є': 'Ye', 'І': 'I', 'Ї': 'Yi', 'Ґ': 'G', 'є': 'ye', 'і': 'i',
        'ї': 'yi', 'ґ': 'g'
    };
    const CZECH_MAP = {
        'č': 'c', 'ď': 'd', 'ě': 'e', 'ň': 'n', 'ř': 'r', 'š': 's', 'ť': 't',
        'ů': 'u', 'ž': 'z', 'Č': 'C', 'Ď': 'D', 'Ě': 'E', 'Ň': 'N', 'Ř': 'R',
        'Š': 'S', 'Ť': 'T', 'Ů': 'U', 'Ž': 'Z'
    };
    const SLOVAK_MAP = {
        'á': 'a', 'ä': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'í': 'i', 'ľ': 'l',
        'ĺ': 'l', 'ň': 'n', 'ó': 'o', 'ô': 'o', 'ŕ': 'r', 'š': 's', 'ť': 't',
        'ú': 'u', 'ý': 'y', 'ž': 'z',
        'Á': 'a', 'Ä': 'A', 'Č': 'C', 'Ď': 'D', 'É': 'E', 'Í': 'I', 'Ľ': 'L',
        'Ĺ': 'L', 'Ň': 'N', 'Ó': 'O', 'Ô': 'O', 'Ŕ': 'R', 'Š': 'S', 'Ť': 'T',
        'Ú': 'U', 'Ý': 'Y', 'Ž': 'Z'
    };
    const POLISH_MAP = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's',
        'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S',
        'Ź': 'Z', 'Ż': 'Z'
    };
    const LATVIAN_MAP = {
        'ā': 'a', 'č': 'c', 'ē': 'e', 'ģ': 'g', 'ī': 'i', 'ķ': 'k', 'ļ': 'l',
        'ņ': 'n', 'š': 's', 'ū': 'u', 'ž': 'z',
        'Ā': 'A', 'Č': 'C', 'Ē': 'E', 'Ģ': 'G', 'Ī': 'I', 'Ķ': 'K', 'Ļ': 'L',
        'Ņ': 'N', 'Š': 'S', 'Ū': 'U', 'Ž': 'Z'
    };
    const ARABIC_MAP = {
        'أ': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'g', 'ح': 'h', 'خ': 'kh', 'د': 'd',
        'ذ': 'th', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't',
        'ظ': 'th', 'ع': 'aa', 'غ': 'gh', 'ف': 'f', 'ق': 'k', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'o', 'ي': 'y'
    };
    const LITHUANIAN_MAP = {
        'ą': 'a', 'č': 'c', 'ę': 'e', 'ė': 'e', 'į': 'i', 'š': 's', 'ų': 'u',
        'ū': 'u', 'ž': 'z',
        'Ą': 'A', 'Č': 'C', 'Ę': 'E', 'Ė': 'E', 'Į': 'I', 'Š': 'S', 'Ų': 'U',
        'Ū': 'U', 'Ž': 'Z'
    };
    const SERBIAN_MAP = {
        'ђ': 'dj', 'ј': 'j', 'љ': 'lj', 'њ': 'nj', 'ћ': 'c', 'џ': 'dz',
        'đ': 'dj', 'Ђ': 'Dj', 'Ј': 'j', 'Љ': 'Lj', 'Њ': 'Nj', 'Ћ': 'C',
        'Џ': 'Dz', 'Đ': 'Dj'
    };
    const AZERBAIJANI_MAP = {
        'ç': 'c', 'ə': 'e', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ə': 'E', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    };
    const GEORGIAN_MAP = {
        'ა': 'a', 'ბ': 'b', 'გ': 'g', 'დ': 'd', 'ე': 'e', 'ვ': 'v', 'ზ': 'z',
        'თ': 't', 'ი': 'i', 'კ': 'k', 'ლ': 'l', 'მ': 'm', 'ნ': 'n', 'ო': 'o',
        'პ': 'p', 'ჟ': 'j', 'რ': 'r', 'ს': 's', 'ტ': 't', 'უ': 'u', 'ფ': 'f',
        'ქ': 'q', 'ღ': 'g', 'ყ': 'y', 'შ': 'sh', 'ჩ': 'ch', 'ც': 'c', 'ძ': 'dz',
        'წ': 'w', 'ჭ': 'ch', 'ხ': 'x', 'ჯ': 'j', 'ჰ': 'h'
    };

    const ALL_DOWNCODE_MAPS = [
        LATIN_MAP,
        LATIN_SYMBOLS_MAP,
        GREEK_MAP,
        TURKISH_MAP,
        ROMANIAN_MAP,
        RUSSIAN_MAP,
        UKRAINIAN_MAP,
        CZECH_MAP,
        SLOVAK_MAP,
        POLISH_MAP,
        LATVIAN_MAP,
        ARABIC_MAP,
        LITHUANIAN_MAP,
        SERBIAN_MAP,
        AZERBAIJANI_MAP,
        GEORGIAN_MAP
    ];

    const Downcoder = {
        'Initialize': function() {
            if (Downcoder.map) { // already made
                return;
            }
            Downcoder.map = {};
            for (const lookup of ALL_DOWNCODE_MAPS) {
                Object.assign(Downcoder.map, lookup);
            }
            Downcoder.regex = new RegExp(Object.keys(Downcoder.map).join('|'), 'g');
        }
    };

    function downcode(slug) {
        Downcoder.Initialize();
        return slug.replace(Downcoder.regex, function(m) {
            return Downcoder.map[m];
        });
    }


    function URLify(s, num_chars, allowUnicode) {
        // changes, e.g., "Petty theft" to "petty-theft"
        if (!allowUnicode) {
            s = downcode(s);
        }
        s = s.toLowerCase(); // convert to lowercase
        // if downcode doesn't hit, the char will be stripped here
        if (allowUnicode) {
            // Keep Unicode letters including both lowercase and uppercase
            // characters, whitespace, and dash; remove other characters.
            s = XRegExp.replace(s, XRegExp('[^-_\\p{L}\\p{N}\\s]', 'g'), '');
        } else {
            s = s.replace(/[^-\w\s]/g, ''); // remove unneeded chars
        }
        s = s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
        s = s.replace(/[-\s]+/g, '-'); // convert spaces to hyphens
        s = s.substring(0, num_chars); // trim to first num_chars chars
        return s.replace(/-+$/g, ''); // trim any trailing hyphens
    }
    window.URLify = URLify;
}

```

# staticfiles/css/styles.css

```css
.alert {
    animation: fadeIn 1s ease, fadeOut 5s ease 8s;
    transition: all 0.3s ease-in-out;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeOut {
    from {
        opacity: 1;
        transform: translateY(0);
    }
    to {
        opacity: 0;
        transform: translateY(-20px);
    }
}

#modal-alert {
    transition: all 0.3s ease-in-out;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}

.is-invalid {
    border-color: #dc3545;
    box-shadow: 0 0 5px rgba(220, 53, 69, 0.75);
}

.invalid-feedback {
    color: #dc3545;
    font-size: 0.9rem;
}

.alert {
    animation: fadeIn 0.5s ease-in-out, fadeOut 5s ease-out 8s;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeOut {
    from {
        opacity: 1;
        transform: translateY(0);
    }
    to {
        opacity: 0;
        transform: translateY(-10px);
    }
}

```

# staticfiles/js/scripts.js

```js

```

# supplier_regulations/Code.pdf

This is a binary file of the type: PDF

# t

```

```

# testapp/__init__.py

```py
default_app_config = 'testapp.apps.TestappConfig'

```

# testapp/admin.py

```py
from django.contrib import admin
from .models import item, Supplier, Product, Invoice, InvoiceProduct

# Register your models here.
admin.site.register(item)  # Test model
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(InvoiceProduct)

```

# testapp/apps.py

```py
from django.apps import AppConfig


class TestappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testapp'

    def ready(self):
        import testapp.signals

```

# testapp/base.py

```py
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

```

# testapp/forms.py

```py
from django import forms
from .models import Invoice, InvoiceProduct, Product
from django.forms.models import inlineformset_factory
from decimal import Decimal

# Define the inline formset for linking Invoice and InvoiceProduct
InvoiceProductFormset = inlineformset_factory(
    Invoice,
    InvoiceProduct,
    fields=['product', 'quantity', 'unit_price', 'reduction_rate', 'vat_rate'],
    extra=1,  # Number of empty forms to display initially
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01'}),
        'reduction_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        'vat_rate': forms.Select(attrs={'class': 'form-control'}),
    }
)

class InvoiceCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        print("INITIALIZING CREATE FORM")  # Debug print
        super().__init__(*args, **kwargs)
        print(f"CREATE FORM fields: {self.fields}")  # Debug print

    class Meta:
        model = Invoice
        fields = ['ref', 'date', 'supplier']
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

class InvoiceUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        print("INITIALIZING UPDATE FORM")  # Debug print
        super().__init__(*args, **kwargs)
        print(f"UPDATE FORM Before disable: {self.fields}")  # Debug print
        self.fields['supplier'].disabled = True
        print(f"UPDATE FORM After disable: {self.fields}")  # Debug print

    class Meta:
        model = Invoice
        fields = ['ref', 'date', 'supplier']
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['supplier'] = self.instance.supplier
        return cleaned_data
        

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
        widgets = {
            'vat_rate': forms.Select(choices=[
                ('0.00', '0%'), 
                ('7.00', '7%'), 
                ('10.00', '10%'), 
                ('11.00', '11%'), 
                ('14.00', '14%'), 
                ('16.00', '16%'), 
                ('20.00', '20%')
            ])
        }
```

# testapp/middleware.py

```py
from django.shortcuts import redirect

class RedirectIfNotLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is not authenticated and is trying to access profile
        if not request.user.is_authenticated and request.path == '/profile/':
            return redirect('login')  # Redirect to login page

        # Otherwise, proceed as normal
        response = self.get_response(request)
        return response

```

# testapp/migrations/__init__.py

```py

```

# testapp/migrations/0001_initial.py

```py
# Generated by Django 4.2.16 on 2024-11-03 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]

```

# testapp/migrations/0002_item_created_at_item_updated_at_alter_item_id.py

```py
# Generated by Django 4.2.16 on 2024-11-03 15:03

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='item',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]

```

# testapp/migrations/0003_profile.py

```py
# Generated by Django 4.2.16 on 2024-11-03 21:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('testapp', '0002_item_created_at_item_updated_at_alter_item_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('position', models.CharField(max_length=100)),
                ('date_of_joining', models.DateField()),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('contact_number', models.CharField(blank=True, max_length=15)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

```

# testapp/migrations/0004_alter_profile_date_of_joining.py

```py
# Generated by Django 4.2.16 on 2024-11-03 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0003_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='date_of_joining',
            field=models.DateField(blank=True, null=True),
        ),
    ]

```

# testapp/migrations/0005_invoice_product_supplier_invoiceproduct_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-07 23:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0004_alter_profile_date_of_joining'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ref', models.CharField(max_length=50, unique=True)),
                ('date', models.DateField()),
                ('fiscal_label', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=4)),
                ('expense_code', models.CharField(max_length=20)),
                ('is_energy', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('if_code', models.CharField(max_length=20, unique=True)),
                ('ice_code', models.CharField(max_length=15, unique=True)),
                ('rc_code', models.CharField(max_length=20)),
                ('rc_center', models.CharField(max_length=100)),
                ('accounting_code', models.CharField(max_length=20, unique=True)),
                ('is_energy', models.BooleanField(default=False)),
                ('service', models.CharField(max_length=255)),
                ('delay_convention', models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)),
                ('is_regulated', models.BooleanField(default=False)),
                ('regulation_file_path', models.FileField(blank=True, null=True, upload_to='supplier_regulations/')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvoiceProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reduction_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=4)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='testapp.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testapp.product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='invoice',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testapp.supplier'),
        ),
    ]

```

# testapp/migrations/0006_alter_invoiceproduct_quantity_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-08 00:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0005_invoice_product_supplier_invoiceproduct_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceproduct',
            name='quantity',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='reduction_rate',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)]),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='vat_rate',
            field=models.DecimalField(choices=[(7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='product',
            name='expense_code',
            field=models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='vat_rate',
            field=models.DecimalField(choices=[(7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='accounting_code',
            field=models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='ice_code',
            field=models.CharField(max_length=15, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='if_code',
            field=models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='name',
            field=models.CharField(max_length=100, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='rc_center',
            field=models.CharField(max_length=100, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='rc_code',
            field=models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='service',
            field=models.CharField(blank=True, max_length=255, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')]),
        ),
    ]

```

# testapp/migrations/0007_invoice_payment_due_date_invoice_status_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-08 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0006_alter_invoiceproduct_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft', max_length=20),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=20.0, max_digits=5),
        ),
    ]

```

# testapp/migrations/0008_product_fiscal_label_alter_invoiceproduct_vat_rate_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-17 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0007_invoice_payment_due_date_invoice_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='fiscal_label',
            field=models.CharField(default='TEST', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='vat_rate',
            field=models.DecimalField(choices=[(0.0, '0%'), (7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='product',
            name='vat_rate',
            field=models.DecimalField(choices=[(0.0, '0%'), (7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5),
        ),
    ]

```

# testapp/migrations/0009_remove_invoice_fiscal_label.py

```py
# Generated by Django 4.2.16 on 2024-11-18 21:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0008_product_fiscal_label_alter_invoiceproduct_vat_rate_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='fiscal_label',
        ),
    ]

```

# testapp/migrations/0010_invoice_exported_at_exportrecord_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-20 23:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('testapp', '0009_remove_invoice_fiscal_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='exported_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ExportRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exported_at', models.DateTimeField(auto_now_add=True)),
                ('filename', models.CharField(max_length=255)),
                ('note', models.TextField(blank=True)),
                ('exported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='invoice',
            name='export_history',
            field=models.ManyToManyField(blank=True, related_name='invoices', to='testapp.exportrecord'),
        ),
    ]

```

# testapp/migrations/0011_alter_supplier_name_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-21 21:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0010_invoice_exported_at_exportrecord_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='name',
            field=models.CharField(max_length=100, unique=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(fields=('supplier', 'ref'), name='unique_supplier_invoice_ref'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('name', 'expense_code'), name='unique_product_name_expense_code'),
        ),
        migrations.AddConstraint(
            model_name='supplier',
            constraint=models.UniqueConstraint(fields=('name', 'rc_code'), name='unique_supplier_name_rc_code'),
        ),
    ]

```

# testapp/migrations/0012_alter_invoice_supplier_alter_invoiceproduct_product.py

```py
# Generated by Django 4.2.16 on 2024-11-21 21:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0011_alter_supplier_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.supplier'),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.product'),
        ),
    ]

```

# testapp/migrations/0013_alter_invoice_options.py

```py
# Generated by Django 4.2.16 on 2024-11-22 18:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0012_alter_invoice_supplier_alter_invoiceproduct_product'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'permissions': [('can_export_invoice', 'Can export invoice'), ('can_unexport_invoice', 'Can unexport invoice')]},
        ),
    ]

```

# testapp/migrations/0014_checker_check_check_check_amount_cannot_exceed_due.py

```py
# Generated by Django 4.2.16 on 2024-11-22 22:41

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0013_alter_invoice_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Checker',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(blank=True, max_length=10, unique=True)),
                ('type', models.CharField(choices=[('CHQ', 'Cheque'), ('LCN', 'LCN')], max_length=3)),
                ('bank', models.CharField(choices=[('ATW', 'Attijariwafa Bank'), ('BCP', 'Banque Populaire'), ('BOA', 'Bank of Africa'), ('CAM', 'Crédit Agricole du Maroc'), ('CIH', 'CIH Bank'), ('BMCI', 'BMCI'), ('SGM', 'Société Générale Maroc'), ('CDM', 'Crédit du Maroc'), ('ABB', 'Al Barid Bank'), ('CFG', 'CFG Bank'), ('ABM', 'Arab Bank Maroc'), ('CTB', 'Citibank Maghreb')], max_length=4)),
                ('account_number', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^\\d+$', 'Only numeric characters allowed.')])),
                ('city', models.CharField(max_length=50, validators=[django.core.validators.RegexValidator('^[A-Za-z\\s]+$', 'Only alphabetical characters allowed.')])),
                ('owner', models.CharField(default='Briqueterie Sidi Kacem', max_length=100)),
                ('num_pages', models.IntegerField(choices=[(25, '25'), (50, '50'), (100, '100')])),
                ('index', models.CharField(max_length=3, validators=[django.core.validators.RegexValidator('^[A-Z]{3}$', 'Must be 3 uppercase letters.')])),
                ('starting_page', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('final_page', models.IntegerField(blank=True)),
                ('current_position', models.IntegerField(blank=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('position', models.CharField(max_length=10)),
                ('creation_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_due', models.DateField(blank=True, null=True)),
                ('amount_due', models.DecimalField(decimal_places=2, editable=False, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('observation', models.TextField(blank=True)),
                ('delivered', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('beneficiary', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.supplier')),
                ('cause', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.invoice')),
                ('checker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checks', to='testapp.checker')),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='check',
            constraint=models.CheckConstraint(check=models.Q(('amount__lte', models.F('amount_due'))), name='check_amount_cannot_exceed_due'),
        ),
    ]

```

# testapp/migrations/0015_check_cancellation_reason_check_cancelled_at_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-23 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0014_checker_check_check_check_amount_cannot_exceed_due"),
    ]

    operations = [
        migrations.AddField(
            model_name="check",
            name="cancellation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="check",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="check",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="check",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="check",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("delivered", "Delivered"),
                    ("paid", "Paid"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]

```

# testapp/migrations/0016_invoice_payment_status_alter_checker_index.py

```py
# Generated by Django 4.2.16 on 2024-11-24 12:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0015_check_cancellation_reason_check_cancelled_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_status',
            field=models.CharField(choices=[('not_paid', 'Not Paid'), ('partially_paid', 'Partially Paid'), ('paid', 'Paid')], default='not_paid', max_length=20),
        ),
        migrations.AlterField(
            model_name='checker',
            name='index',
            field=models.CharField(max_length=3, validators=[django.core.validators.RegexValidator('^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')]),
        ),
    ]

```

# testapp/models.py

```py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from .base import BaseModel
from datetime import timedelta 
import random
import string
from django.utils import timezone
from decimal import Decimal




class item(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()    
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Supplier(BaseModel):

    numeric_validator = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')
    alphanumeric_validator = RegexValidator(r'^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')

    name = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    if_code = models.CharField(max_length=20, unique=True, validators=[numeric_validator])
    ice_code = models.CharField(max_length=15, unique=True, validators=[numeric_validator])  # Exactly 15 characters
    rc_code = models.CharField(max_length=20, validators=[numeric_validator])
    rc_center = models.CharField(max_length=100, validators=[alphanumeric_validator])
    accounting_code = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    service = models.CharField(max_length=255, blank=True, validators=[alphanumeric_validator])  # Description of merch/service sold
    delay_convention = models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)
    is_regulated = models.BooleanField(default=False)
    regulation_file_path = models.FileField(upload_to='supplier_regulations/', null=True, blank=True)

    def clean(self):
        super().clean()
        # Ensure IF code is numeric
        if not self.if_code.isdigit():
            raise ValidationError("IF code must be numeric.")
        # Ensure ICE code has exactly 15 characters
        if len(self.ice_code) != 15:
            raise ValidationError("ICE code must contain exactly 15 characters.")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'rc_code'], name='unique_supplier_name_rc_code')
        ]

    def __str__(self):
        return self.name

class Product(BaseModel):
    name = models.CharField(max_length=100)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, choices=[
    (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
])
    expense_code = models.CharField(max_length=20, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    fiscal_label = models.CharField(max_length=255, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'expense_code'], name='unique_product_name_expense_code')
        ]
    def __str__(self):
        return self.name

class Invoice(BaseModel):
    ref = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft'
    )
    payment_due_date = models.DateField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    export_history = models.ManyToManyField('ExportRecord', blank=True, related_name='invoices')
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid')
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_paid'
    )

    def save(self, *args, **kwargs):
        if not self.payment_due_date:
            self.payment_due_date = self.date + timedelta(days=self.supplier.delay_convention)
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['supplier', 'ref'], name='unique_supplier_invoice_ref')
        ]
        permissions = [
        ("can_export_invoice", "Can export invoice"),
        ("can_unexport_invoice", "Can unexport invoice"),
        ]

    @property
    def fiscal_label(self):
        """Generate a combined fiscal label from all related products."""
        products = [(item.product.fiscal_label, item.quantity * item.unit_price) 
                    for item in self.products.all()]
        unique_labels = []
        seen = set()
        
        # Sort by value and get unique labels
        for label, _ in sorted(products, key=lambda x: x[1], reverse=True):
            if label not in seen:
                unique_labels.append(label)
                seen.add(label)
        
        top_labels = unique_labels[:3]
        if len(unique_labels) > 3:
            top_labels.append('...')
        
        return " - ".join(top_labels)
    
    @property
    def raw_amount(self):
        """Calculate the total amount before tax, considering reduction rate for each product."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100))
                for item in self.products.all()
            ]
        )

    @property
    def total_tax_amount(self):
        """Calculate the total tax amount for the invoice considering different VAT rates."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100) * item.vat_rate / 100)
                for item in self.products.all()
            ]
        )

    @property
    def total_amount(self):
        """Calculate the total amount of the invoice including tax."""
        return self.raw_amount + self.total_tax_amount

    def get_accounting_entries(self):
        entries = []
        expense_groups = {}
        tax_groups = {}
        
        for invoice_product in self.products.all():
            # Group products by expense code
            key = invoice_product.product.expense_code
            if key not in expense_groups:
                expense_groups[key] = {
                    'products': {},  # Changed to dict to track values
                    'amount': 0,
                    'is_energy': invoice_product.product.is_energy
                }
            # Track product value
            product_value = invoice_product.quantity * invoice_product.unit_price * (1 - invoice_product.reduction_rate / 100)
            expense_groups[key]['products'][invoice_product.product.name] = product_value
            expense_groups[key]['amount'] += product_value

            # Group taxes by rate (unchanged)
            tax_key = invoice_product.vat_rate
            if tax_key not in tax_groups:
                tax_groups[tax_key] = 0
            tax_groups[tax_key] += (product_value * invoice_product.vat_rate / 100)

        # Add expense entries with top 3 products by value
        for expense_code, data in expense_groups.items():
            # Sort products by value and get unique names
            sorted_products = sorted(data['products'].items(), key=lambda x: x[1], reverse=True)
            unique_products = []
            seen = set()
            for name, _ in sorted_products:
                if name not in seen:
                    unique_products.append(name)
                    seen.add(name)
            
            product_names = unique_products[:3]
            if len(sorted_products) > 3:
                product_names.append('...')

            entries.append({
                'date': self.date,
                'label': ', '.join(product_names),
                'debit': data['amount'],
                'credit': None,
                'account_code': expense_code,
                'reference': self.ref,
                'journal': '10' if data['is_energy'] else '01',
                'counterpart': ''
            })

        # Rest of the method remains unchanged
        for rate, amount in tax_groups.items():
            if rate > 0:
                entries.append({
                    'date': self.date,
                    'label': f'VAT {int(rate)}%',
                    'debit': amount,
                    'credit': None,
                    'account_code': f'345{int(rate):02d}',
                    'reference': self.ref,
                    'journal': '10' if self.supplier.is_energy else '01',
                    'counterpart': ''
                })

        entries.append({
            'date': self.date,
            'label': self.supplier.name,
            'debit': None,
            'credit': self.total_amount,
            'account_code': self.supplier.accounting_code,
            'reference': self.ref,
            'journal': '10' if self.supplier.is_energy else '01',
            'counterpart': ''
        })

        return entries
    
    def get_payment_details(self):
        """Calculate comprehensive payment details"""
        # Get all non-cancelled checks for this invoice
        valid_checks = Check.objects.filter(
            cause=self
        ).exclude(
            status='cancelled'
        )

        # Calculate various payment amounts
        pending_amount = sum(c.amount for c in valid_checks.filter(status='pending'))
        delivered_amount = sum(c.amount for c in valid_checks.filter(status='delivered'))
        paid_amount = sum(c.amount for c in valid_checks.filter(status='paid'))
        total_issued = sum(c.amount for c in valid_checks)

        # Calculate remaining and percentages
        amount_to_issue = self.total_amount - total_issued
        print(f"Amount to issue: {amount_to_issue}")  # Debug output
        remaining_to_pay = self.total_amount - paid_amount
        print(f"Remaining to pay: {remaining_to_pay}") # Debug output
        payment_percentage = (paid_amount / self.total_amount * 100) if self.total_amount else 0
        print(f"Payment percentage: {payment_percentage}") # Debug output

        details = {
            'total_amount': float(self.total_amount),
            'pending_amount': float(pending_amount),
            'delivered_amount': float(delivered_amount),
            'paid_amount': float(paid_amount),
            'amount_to_issue': float(amount_to_issue),
            'remaining_to_pay': float(remaining_to_pay),
            'payment_percentage': float(payment_percentage),
            'payment_status': self.get_payment_status(paid_amount)
        }

        print(details)  # Debug output
        return details

    def get_payment_status(self, paid_amount=None):
        """Determine payment status based on paid amount"""
        if paid_amount is None:
            paid_amount = sum(c.amount for c in Check.objects.filter(
                cause=self, 
                status='paid'
            ).exclude(status='cancelled'))

        if paid_amount >= self.total_amount:
            return 'paid'
        elif paid_amount > 0:
            return 'partially_paid'
        return 'not_paid'


    @property
    def payments_summary(self):
        payments = Check.objects.filter(cause=self).exclude(status='cancelled')
        return {
            'pending_amount': sum(p.amount for p in payments.filter(status='pending')),
            'delivered_amount': sum(p.amount for p in payments.filter(status='delivered')),
            'paid_amount': sum(p.amount for p in payments.filter(status='paid')),
            'percentage_paid': (sum(p.amount for p in payments.filter(status='paid')) / self.total_amount * 100) if self.total_amount else 0,
            'remaining_amount': self.total_amount - sum(p.amount for p in payments.filter(status='paid')),
            'amount_to_issue': self.total_amount - sum(p.amount for p in payments.exclude(status='cancelled'))
        }

    def update_payment_status(self):
        summary = self.payments_summary
        if summary['paid_amount'] >= self.total_amount:
            self.payment_status = 'paid'
        elif summary['paid_amount'] > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'not_paid'
        self.save()

    def __str__(self):
        return f'Invoice {self.ref} from {self.supplier.name}'

class InvoiceProduct(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reduction_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=[
        (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
    ], default=20.00)

    @property
    def subtotal(self):
        discount = (self.unit_price * self.quantity) * (self.reduction_rate / 100)
        return (self.unit_price * self.quantity) - discount

    @property
    def total_amount(self):
        return self.subtotal + (self.subtotal * (self.vat_rate / 100))

    def save(self, *args, **kwargs):
        if self.vat_rate == 0.00:
            self.vat_rate = self.product.vat_rate
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.product.name} on Invoice {self.invoice.ref}'
    
class ExportRecord(BaseModel):
    exported_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Export {self.filename} at {self.exported_at}"
    
class Checker(BaseModel):
    TYPE_CHOICES = [
        ('CHQ', 'Cheque'),
        ('LCN', 'LCN')
    ]
    
    BANK_CHOICES = [
        ('ATW', 'Attijariwafa Bank'),
        ('BCP', 'Banque Populaire'),
        ('BOA', 'Bank of Africa'),
        ('CAM', 'Crédit Agricole du Maroc'),
        ('CIH', 'CIH Bank'),
        ('BMCI', 'BMCI'),
        ('SGM', 'Société Générale Maroc'),
        ('CDM', 'Crédit du Maroc'),
        ('ABB', 'Al Barid Bank'),
        ('CFG', 'CFG Bank'),
        ('ABM', 'Arab Bank Maroc'),
        ('CTB', 'Citibank Maghreb')
    ]
    
    PAGE_CHOICES = [
        (25, '25'),
        (50, '50'),
        (100, '100')
    ]

    code = models.CharField(max_length=10, unique=True, blank=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    bank = models.CharField(max_length=4, choices=BANK_CHOICES)
    account_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d+$', 'Only numeric characters allowed.')]
    )
    city = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[A-Za-z\s]+$', 'Only alphabetical characters allowed.')]
    )
    owner = models.CharField(max_length=100, default="Briqueterie Sidi Kacem")
    num_pages = models.IntegerField(choices=PAGE_CHOICES)
    index = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')]
    )
    starting_page = models.IntegerField(validators=[MinValueValidator(1)])
    final_page = models.IntegerField(blank=True)
    current_position = models.IntegerField(blank=True)

    @property
    def remaining_pages(self):
        print(f"Calculating remaining pages for {self.bank}")
        print(f"final_page: {self.final_page}")
        print(f"current_position: {self.current_position}")
        return self.final_page - self.current_position + 1

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.final_page:
            self.final_page = self.starting_page + self.num_pages - 1
        if not self.current_position:
            self.current_position = self.starting_page
        print(f"Saving checker for {self.bank}")
        print(f"current_position: {self.current_position}")
        super().save(*args, **kwargs)

    def generate_code(self):
        # Generate random alphanumeric code
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def __str__(self):
        return f'Checker {self.index}'

    class Meta:
        ordering = ['-created_at']

class Check(BaseModel):
    checker = models.ForeignKey(Checker, on_delete=models.PROTECT, related_name='checks')
    position = models.CharField(max_length=10)  # Will store "INDEX + position number"
    creation_date = models.DateField(default=timezone.now)
    beneficiary = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    cause = models.ForeignKey(Invoice, on_delete=models.PROTECT)
    payment_due = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    observation = models.TextField(blank=True)
    delivered = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    
    def save(self, *args, **kwargs):
        print(f"New creation at:  {self.checker.current_position}")
        if not self.position:
            self.position = f"{self.checker.index}{self.checker.current_position}"
        if not self.amount_due:
            self.amount_due = self.cause.total_amount
        super().save(*args, **kwargs)
        
        # Update checker's current position
        if self.checker.current_position == int(self.position[len(self.checker.index):]):
            self.checker.current_position += 1
            self.checker.save()

    def clean(self):
        if self.paid_at and not self.delivered_at:
            raise ValidationError("Check cannot be marked as paid before delivery")

    class Meta:
        ordering = ['-creation_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__lte=models.F('amount_due')),
                name='check_amount_cannot_exceed_due'
            )
        ]
```

# testapp/signals.py

```py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Check

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Create a Profile for new users
        Profile.objects.create(user=instance)
    else:
        # Save the Profile if it already exists
        if hasattr(instance, 'profile'):
            instance.profile.save()


@receiver(post_save, sender=Check)
def update_invoice_payment_status(sender, instance, **kwargs):
    if instance.cause:
        instance.cause.update_payment_status()

```

# testapp/templates/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MyProject{% endblock %}</title>
    
    <!-- Bootstrap 4.5 CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">

    <!-- jQuery and Bootstrap 4.5 JS -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">
</head>
<body>
    <!-- Header / Navigation Bar -->
<header>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <a class="navbar-brand" href="{% url 'login' %}">MyProject</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ml-auto">
                {% if user.is_authenticated %}
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle hover-trigger" href="#" id="supplierDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Supplier
                        </a>
                        <div class="dropdown-menu dropdown-hover" aria-labelledby="supplierDropdown">
                            <a class="dropdown-item hover-highlight" href="{% url 'supplier-list' %}">Suppliers</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'product-list' %}">Products</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'invoice-list' %}">Invoices</a>
                        </div>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle hover-trigger" href="#" id="checkDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Check/Checkers
                        </a>
                        <div class="dropdown-menu dropdown-hover" aria-labelledby="checkDropdown">
                            <a class="dropdown-item hover-highlight" href="{% url 'checker-list' %}">Checkers</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'check-list' %}">Checks</a>
                        </div>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'profile' %}">Profile</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'logout' %}">Logout</a>
                    </li>
                {% else %}
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'login' %}">Login</a>
                    </li>
                {% endif %}
            </ul>
        </div>
    </nav>
</header>

    <!-- Message Alerts -->
    <div id="alerts-container" class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" role="alert">
                    {% if message.tags == 'error' %}
                        <i class="fas fa-exclamation-triangle"></i>
                    {% endif %}
                    <strong>{{ message|safe }}</strong>
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Main Content Block -->
    <main class="container mt-4">
        {% block content %}
        <!-- Page-specific content goes here -->
        {% endblock %}
    </main>

    <!-- Footer -->
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">&copy; 2024 MyProject. All rights reserved.</span>
            <div>
                <a href="#" class="text-muted mx-2">Privacy</a>
                <a href="#" class="text-muted mx-2">Terms</a>
                <a href="#" class="text-muted mx-2">Support</a>
            </div>
        </div>
    </footer>

    <!-- Custom JavaScript -->
    <script src="{% static 'js/scripts.js' %}"></script>

    <script>
        // Fading Alerts
        $(document).ready(function() {
            setTimeout(function() {
                $(".alert").fadeOut("slow");
            }, 5000);

            // Dropdown on Hover
            $(".hover-trigger").hover(function() {
                $(this).parent().addClass('show');
                $(this).siblings('.dropdown-menu').addClass('show').stop(true, true).slideDown(200);
            }, function() {
                $(this).parent().removeClass('show');
                $(this).siblings('.dropdown-menu').removeClass('show').stop(true, true).slideUp(200);
            });

            $(".dropdown-menu").hover(function() {
                $(this).addClass('show').stop(true, true).slideDown(200);
            }, function() {
                $(this).removeClass('show').stop(true, true).slideUp(200);
            });
        });
    </script>

    <style>
        /* Alert Styling */
        .alert {
            border-left: 5px solid;
        }
        .alert-danger {
            border-left-color: #dc3545;
        }
        .alert i {
            margin-right: 10px;
        }

        /* Navbar Hover Effects */
        .hover-trigger:hover {
            background-color: rgba(159, 165, 174, 0.2);
            transition: background-color 0.3s ease;
            text-decoration:underline;
        }

        /* Dropdown Menu Styling */
        .dropdown-menu {
            display: none;
        }
        .hover-highlight:hover {
            background-color: rgba(200, 52, 203, 0.1);
            transition: background-color 0.3s ease;
        }

        /* Footer Styling */
        .footer a {
            margin: 0 5px;
            color: inherit;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</body>
</html>

```

# testapp/templates/checker/check_list.html

```html
{% extends 'base.html' %}

{% load check_tags %}

{% block content %}
<div class="container mt-4">
    <h2>Checks List</h2>
    <div class="container-fluid px-1">  <!-- Add padding -->
        <div class="table-responsive">  <!-- Make table responsive -->
            <table class="table table-hover">
                <thead class="thead-dark">
                    <tr>
                        <th>Checker Code</th>
                        <th>Bank</th>
                        <th>Owner</th>
                        <th>Type</th>
                        <th>Position</th>
                        <th>Creation Date</th>
                        <th>Beneficiary</th>
                        <th>Invoice Ref</th>
                        <th>Payment Due</th>
                        <th>Amount Due</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for check in checks %}
                    <tr {% if check.cancelled_at %}class="table-danger" data-cancelled="true" data-cancel-reason="{{ check.cancellation_reason }}"{% endif %}>
                        <td>{{ check.checker.code }}</td>
                        <td>{{ check.checker.get_bank_display }}</td>
                        <td>{{ check.checker.owner }}</td>
                        <td>{{ check.checker.get_type_display }}</td>
                        <td>{{ check.position }}</td>
                        <td>{{ check.creation_date|date:"Y-m-d" }}</td>
                        <td>{{ check.beneficiary.name }}</td>
                        <td>{{ check.cause.ref }}</td>
                        <td>{{ check.payment_due|date:"Y-m-d"|default:"-" }}</td>
                        <td class="text-right">{{ check.amount_due|floatformat:2 }}</td>
                        <td class="text-right">{{ check.amount|floatformat:2 }}</td>
                        <td>
                            {% if check.status == 'cancelled' %}
                            <span class="badge badge-danger cancellation-info" 
                                    role="button" 
                                    data-toggle="modal" 
                                    data-target="#cancellationDetailModal"
                                    data-reason="{{ check.cancellation_reason }}">
                                Cancelled
                            </span>
                            {% elif check.paid %}
                                <span class="badge badge-success">Paid</span>
                            {% elif check.delivered %}
                                <span class="badge badge-warning">Delivered</span>
                            {% else %}
                                <span class="badge badge-secondary">Pending</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-primary btn-sm edit-check-btn" 
                                        data-check-id="{{ check.id }}">
                                    Edit
                                </button>
                                {% if not check.delivered %}
                                    <button class="btn btn-warning btn-sm mark-delivered" 
                                            data-check="{{ check.id }}">
                                        Mark Delivered
                                    </button>
                                {% endif %}
                                {% if check.delivered and not check.paid %}
                                    <button class="btn btn-success btn-sm mark-paid" 
                                            data-check="{{ check.id }}">
                                        Mark Paid
                                    </button>
                                {% endif %}
                                {% if not check.paid %}
                                    <button class="btn btn-danger btn-sm cancel-check-btn" 
                                            data-check-id="{{ check.id }}">
                                        Cancel
                                    </button>
                                {% endif %}
                                <button class="btn btn-info btn-sm">Print</button>
                            </div>
                        </td>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="modal fade" id="editCheckModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Check</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <form id="edit-check-form">
                    <div class="form-group">
                        <label>Status: <span class="badge" id="check-status-badge"></span></label>
                    </div>
                    <div class="form-group">
                        <label for="delivered_at">Delivered At:</label>
                        <input type="datetime-local" id="delivered_at" class="form-control">
                    </div>
                    <div class="form-group">
                        <label for="paid_at">Paid At:</label>
                        <input type="datetime-local" id="paid_at" class="form-control">
                    </div>
                    
                    <!-- Cancel Check Button (only shown if not paid) -->
                    <div class="form-group" id="cancel-check-section">
                        <button type="button" class="btn btn-danger" id="cancel-check-btn">
                            Cancel Check
                        </button>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" id="save-check-btn">Save Changes</button>
            </div>
        </div>
    </div>
</div>

<!-- Cancellation Modal -->
<div class="modal fade" id="cancelCheckModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancel Check</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="cancellation_reason">Reason for Cancellation:</label>
                    <textarea id="cancellation_reason" class="form-control" placeholder="Reason for cancellation" rows="2" required ></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirm-cancel-btn">Confirm Cancellation</button>
            </div>
        </div>
    </div>
</div>

<!-- Add this modal to your template -->
<div class="modal fade" id="cancellationDetailModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancellation Reason</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <p id="cancellationReason"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<style>
    .cancellation-info {
        cursor: pointer;
    }
    .cancellation-info:hover {
        opacity: 0.8;
    }
    
    /* Make buttons more refined */
    .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        border-radius: 0.25rem;
        transition: all 0.2s;
    }
    
    .btn i {
        font-size: 0.875rem;
    }
    
    .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Space out buttons in button groups */
    .btn-group .btn {
        margin-right: 0.25rem;
    }
    .btn-group .btn:last-child {
        margin-right: 0;
    }

    .table-responsive {
    margin: 0 auto;
    padding: 10px;
    overflow-x: auto;
    overflow-y: auto;

    }
</style>

<script>
$(document).ready(function() {
    let currentCheckId;

    // Disable controls for cancelled checks
    $('tr[data-cancelled="true"]').each(function() {
        const reason = $(this).data('cancel-reason');
        $(this).find('button').prop('disabled', true)
            .attr('title', `Check cancelled: ${reason}`);
    });

    $('.mark-delivered').click(function() {
        const checkId = $(this).data('check');
        if (confirm('Mark this check as delivered?')) {
            $.ajax({
                url: `/testapp/checks/${checkId}/mark-delivered/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error marking check as delivered');
                }
            });
        }
    });

    $('.mark-paid').click(function() {
        const checkId = $(this).data('check');
        if (confirm('Mark this check as paid?')) {
            $.ajax({
                url: `/testapp/checks/${checkId}/mark-paid/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error marking check as paid');
                }
            });
        }
    });

     // Edit Check Modal
    $('.edit-check-btn').click(function() {
        const $row = $(this).closest('tr');
        if ($row.data('cancelled')) {
            alert(`Check cancelled: ${$row.data('cancel-reason')}`);
            return;
        }

        currentCheckId = $(this).data('check-id');
        console.log("Opening edit modal for check:", currentCheckId);
        
        $.ajax({
            url: `/testapp/checks/${currentCheckId}/`,
            method: 'GET',
            success: function(data) {
                console.log("Received data:", data); // Debug
                $('#delivered_at').val(data.delivered_at)
                    .prop('readonly', data.delivered_at != null);
                $('#paid_at').val(data.paid_at)
                    .prop('readonly', data.paid_at != null);
                
                // Update status badge
                const badgeClass = {
                    'pending': 'badge-warning',
                    'delivered': 'badge-info',
                    'paid': 'badge-success',
                    'cancelled': 'badge-danger'
                }[data.status];
            
                
                $('#check-status-badge')
                    .text(data.status.toUpperCase())
                    .removeClass()
                    .addClass(`badge ${badgeClass}`);
                
                // Show/hide cancel section based on status
                $('#cancel-section').toggle(!data.paid_at);
                $('#save-check-btn').prop('disabled', data.cancelled_at);
                
                $('#editCheckModal').modal('show');
            },
            error: function(xhr) {
                alert("Error loading check details");
            }
        });
    });
    
    // Save Check Changes
    $('#save-check-btn').click(function() {
        console.log("Saving changes for check:", currentCheckId);   

        $.ajax({
            url: `/testapp/checks/${currentCheckId}/`,
            method: 'POST',
            data: JSON.stringify({
                delivered_at: $('#delivered_at').val(),
                paid_at: $('#paid_at').val()
            }),
            contentType: 'application/json',
            success: function() {
                $('#editCheckModal').modal('hide');
                location.reload();
            },
            error: function(xhr) {
                alert(xhr.responseJSON.error|| "Error saving changes");
            }
        });
    });
    
    // Cancel Check
    $('#cancel-check-btn').click(function() {
        $('#editCheckModal').modal('hide');
        $('#cancelCheckModal').modal('show');
    });
    
    // Confirm Cancellation
    $('#confirm-cancel-btn').click(function() {
        const reason = $('#cancellation_reason').val();
        
        if (!reason.trim()) {
            alert('Please provide a reason for cancellation');
            return;
        }

        console.log("Cancelling check:", currentCheckId);
        $.ajax({
            url: `/testapp/checks/${currentCheckId}/cancel/`,
            method: 'POST',
            data: JSON.stringify({ reason: reason }),
            contentType: 'application/json',
            success: function() {
                $('#cancelCheckModal').modal('hide');
                location.reload();
            },
            error: function(xhr) {
                alert(xhr.responseJSON.error || "Error cancelling check");
            }
        });
    });

    // Display cancellation reason
    $('.cancellation-info').click(function() {
        const reason = $(this).data('reason');
        $('#cancellationReason').text(reason);
    });

    // Reset modals on close
    $('#editCheckModal, #cancelCheckModal').on('hidden.bs.modal', function() {
        $('#cancellation_reason').val('');
    });
});
</script>
{% endblock %}
```

# testapp/templates/checker/checker_list.html

```html
{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Checkers</h2>
        <button class="btn btn-primary" data-toggle="modal" data-target="#checkerModal">
            <i class="fas fa-plus"></i> Add New Checker
        </button>
    </div>

    <table class="table table-hover">
        <thead class="thead-dark">
            <tr>
                <th>Code</th>
                <th>Owner</th>
                <th>Type</th>
                <th>Bank</th>
                <th>Account</th>
                <th>City</th>
                <th>Starting Page</th>
                <th>Final Page</th>
                <th>Current Position</th>
                <th>Remaining Pages</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for checker in checkers %}
            <tr>
                <td>{{ checker.code }}</td>
                <td>{{ checker.owner }}</td>
                <td>{{ checker.get_type_display }}</td>
                <td>{{ checker.get_bank_display }}</td>
                <td>{{ checker.account_number }}</td>
                <td>{{ checker.city }}</td>
                <td>{{ checker.index }}{{ checker.starting_page }}</td>
                <td>{{ checker.index }}{{ checker.final_page }}</td>
                <td>{{ checker.index }}{{ checker.current_position }}</td>
                <td>{{ checker.remaining_pages }}</td>
                <td>
                    <button class="btn btn-primary btn-sm add-payment" data-checker="{{ checker.id }}">
                        <i class="fas fa-plus"></i> Add Payment
                    </button>
                    <button class="btn btn-info btn-sm view-details" data-checker="{{ checker.id }}">
                        Details
                    </button>
                    <button class="btn btn-danger btn-sm delete-checker" data-checker="{{ checker.id }}">
                        <i class="fas fa-times"></i> Delete
                    </button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Checker Modal -->
<div class="modal fade" id="checkerModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add New Checker</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form id="checker-form">
                    <div class="form-group">
                        <label>Type</label>
                        <select class="form-control" name="type" required>
                            <option value="CHQ">Cheque</option>
                            <option value="LCN">LCN</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Bank</label>
                        <select class="form-control" name="bank" required>
                            {% for code, name in bank_choices %}
                            <option value="{{ code }}">{{ name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Account Number</label>
                        <input type="text" id="account_number" name="account_number" 
                            class="form-control" 
                            pattern="\d+" 
                            oninput="this.value = this.value.replace(/[^0-9]/g, '')"
                            title="Only numbers allowed"
                            required>
                    </div>
                    <div class="form-group">
                        <label>City</label>
                        <input type="text" class="form-control" name="city" 
                               pattern="^[A-Za-z\s]+$" required>
                    </div>
                    <div class="form-group">
                        <label>Number of Pages</label>
                        <select class="form-control" name="num_pages" required>
                            <option value="25">25</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Index (3 uppercase letters)</label>
                        <input type="text" class="form-control" name="index" 
                               pattern="^[A-Z]{3}$" required>
                    </div>
                    <div class="form-group">
                        <label>Starting Page</label>
                        <input type="number" class="form-control" name="starting_page" 
                               min="1" required>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" id="save-checker">Save</button>
            </div>
        </div>
    </div>
</div>

<!-- Payment Modal -->
<div class="modal fade" id="paymentModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Payment</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form id="payment-form">
                    <input type="hidden" id="checker_id" name="checker_id">
                    <div class="form-group">
                        <label>Position</label>
                        <input type="text" class="form-control" id="position" disabled>
                    </div>
                    <div class="form-group">
                        <label>Creation Date</label>
                        <input type="date" class="form-control" name="creation_date" 
                               value="{% now 'Y-m-d' %}">
                    </div>
                    <div class="form-group">
                        <label>Beneficiary</label>
                        <input type="text" class="form-control" id="beneficiary" 
                               placeholder="Search supplier...">
                        <input type="hidden" id="supplier_id">
                    </div>
                    <div class="form-group">
                        <label>Invoice</label>
                        <input type="text" class="form-control" id="invoice" 
                               placeholder="Search invoice..." disabled>
                        <input type="hidden" id="invoice_id" name="invoice_id">
                    </div>
                    <div class="form-group">
                        <label>Payment Due Date</label>
                        <input type="date" class="form-control" name="payment_due">
                    </div>
                    <div class="form-group">
                        <label>Amount Due</label>
                        <input type="number" class="form-control" id="amount_due" disabled>
                    </div>
                    <div class="form-group">
                        <label>Amount</label>
                        <input type="number" class="form-control" name="amount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Observation</label>
                        <textarea class="form-control" name="observation"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-success" id="save-and-clone">Save and Clone</button>
                <button type="button" class="btn btn-primary" id="save-payment">Save</button>
            </div>
        </div>
    </div>
</div>

<style>
    .ui-autocomplete {
        position: absolute;
        z-index: 2000; /* Make sure it appears above the modal */
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 0;
        max-height: 200px;
        overflow-y: auto;
        list-style: none;
    }

    .ui-menu-item {
        padding: 8px 12px;
        cursor: pointer;
    }

    .ui-menu-item:hover {
        background-color: #f8f9fa;
    }

    .ui-helper-hidden-accessible {
        display: none;
    }
</style>

<script>
$(document).ready(function() {
    console.log("Document ready");

    $('#save-checker').click(function() {
        console.log("Save button clicked"); 
        const form = $('#checker-form');
        const formData = {};
        
        form.serializeArray().forEach(item => {
            formData[item.name] = item.value;
        });

        console.log("Sending data:", formData); // Debug log

        $.ajax({
            url: "{% url 'checker-create' %}",
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            success: function(response) {
                console.log("Success:", response); // Debug log
                location.reload();
            },
            error: function(xhr, status, error) {
                console.error("Error:", xhr.responseText); // Debug log
                alert('Error creating checker: ' + xhr.responseText);
            }
        });
    });

    $('.add-payment').click(function() {
        const checkerId = $(this).data('checker');
        $('#checker_id').val(checkerId);
        
        // Load checker details to get current position
        $.ajax({
            url: `/testapp/checkers/${checkerId}/details/`,
            method: 'GET',
            success: function(data) {
                $('#position').val(`${data.index}${data.current_position}`);
                $('#paymentModal').modal('show');
            }
        });
    });

    // Beneficiary autocomplete
    $('#beneficiary').autocomplete({
        minLength: 2,
        source: function(request, response) {
            $.ajax({
                url: "{% url 'supplier-autocomplete' %}",
                data: { term: request.term },
                success: function(data) {
                    response($.map(data, function(item) {
                        return {
                            label: item.label,
                            value: item.value
                        };
                    }));
                }
            });
        },
        appendTo: "#paymentModal", // Make sure dropdown appears inside modal
        select: function(event, ui) {
            $('#beneficiary').val(ui.item.label.split(' (')[0]);
            $('#supplier_id').val(ui.item.value);
            $('#invoice').prop('disabled', false);
            return false;
        }
    }).data("ui-autocomplete")._renderItem = function(ul, item) {
        return $("<li>")
            .append("<div>" + item.label + "</div>")
            .appendTo(ul);
    };

    // Invoice autocomplete
    $('#invoice').autocomplete({
        minLength: 2,
        source: function(request, response) {
            const supplierId = $('#supplier_id').val();
            console.log("Supplier ID for invoice search:", supplierId);  // Debug
            console.log("Search term:", request.term);  // Debug
            
            if (!supplierId) {
                console.log("No supplier selected");  // Debug
                return;
            }
            
            $.ajax({
                url: "{% url 'invoice-autocomplete' %}",
                data: { 
                    term: request.term,
                    supplier: supplierId
                },
                success: function(data) {
                    console.log("Received invoices:", data);  // Debug
                    response($.map(data, function(item) {
                        console.log("Mapping item:", item);  // Debug
                        return {
                            label: item.label,
                            value: item.value,
                            amount: item.amount
                        };
                    }));
                },
                error: function(xhr, status, error) {
                    console.error("Invoice search error:", error);  // Debug
                    console.error("Response:", xhr.responseText);  // Debug
                }
            });
        },
        select: function(event, ui) {
            console.log("Selected invoice:", ui.item);  // Debug
            $('#invoice').val(ui.item.label.split(' (')[0]);
            $('#invoice_id').val(ui.item.value);
            $('#amount_due').val(ui.item.amount);
            $('input[name="amount"]').val(ui.item.amount);
            return false;
        }
    });

    $('#save-payment').click(function() {
        const form = $('#payment-form');
        const formData = {};
        
        form.serializeArray().forEach(item => {
            formData[item.name] = item.value;
        });

        $.ajax({
            url: "{% url 'check-create' %}",
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        },
            success: function(response) {
                location.reload();
            },
            error: function(xhr) {
                alert(xhr.responseJSON.error);
            }
        });
    });
    $('.delete-checker').click(function() {
        if (confirm('Are you sure you want to delete this checker?')) {
            const checkerId = $(this).data('checker');
            $.ajax({
                url: `/testapp/checkers/${checkerId}/delete/`,
                method: 'POST',
                headers: {'X-CSRFToken': '{{ csrf_token }}'},
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert(xhr.responseJSON.error);
                }
            });
        }
    });
});
</script>
{% endblock %}
```

# testapp/templates/home.html

```html
{% extends 'base.html' %}

{% block title %}Home - MyProject{% endblock %}

{% block content %}
<h1>Welcome to MyProject!</h1>
<p>This is the home page.</p>
{% endblock %}

```

# testapp/templates/invoice/invoice_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Invoice{% endblock %}

{% block content %}
<h1>Delete Invoice</h1>
<p>Are you sure you want to delete the invoice with reference "{{ invoice.ref }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'invoice-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/invoice/invoice_form.html

```html
{% extends 'base.html' %}
{% load humanize %}
{% load accounting_filters %}


{% block title %}Invoice Form{% endblock %}

{% block content %}
<h1>{{ view.object.pk|default:'Add New Invoice' }}</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    {{ products.management_form }}

    <div style="display: none;">
        {% for product_form in products %}
            <div class="product-form">
                {{ product_form.id }}
                {{ product_form.product }}
                {{ product_form.quantity }}
                {{ product_form.unit_price }}
                {{ product_form.reduction_rate }}
                {{ product_form.vat_rate }}
                {% if product_form.instance.pk %}{{ product_form.DELETE }}{% endif %}
            </div>
        {% endfor %}
    </div>
    
    <button type="submit" class="btn btn-success mt-4">Save</button>
    <a href="{% url 'invoice-list' %}" class="btn btn-secondary mt-4">Cancel</a>
</form>

<!-- Add Product Button after Invoice is saved -->
{% if view.object.pk %}
    <button type="button" id="add-product" class="btn btn-primary mt-4" data-toggle="modal" data-target="#productModal">Add Product</button>

    <!-- Table to show all products linked to the current invoice -->
    <h3 class="mt-4">Products in Invoice</h3>
    <table class="table table-hover table-bordered mt-2">
        <thead class="thead-dark">
            <tr>
                <th>Product</th>
                <th>Fiscal Label</th>
                <th>Expense Code</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Reduction Rate (%)</th>
                <th>VAT Rate (%)</th>
                <th>Subtotal</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="product-list">
            {% for product in view.object.products.all %}
            <tr data-product-id="{{ product.pk }}">
                <td>{{ product.product.name }}</td>
                <td>{{ product.product.fiscal_label }}</td>
                <td>{{ product.product.expense_code }}</td> 
                <td>{{ product.quantity }}</td>
                <td>{{ product.unit_price|space_thousands }}</td>
                <td>{{ product.reduction_rate }}</td>
                <td>{{ product.vat_rate }}</td>
                <td>{{ product.subtotal|space_thousands }}</td>
                <td>
                    <button class="btn btn-warning btn-sm edit-product" data-product-id="{{ product.pk }}">Edit</button>
                    <button class="btn btn-danger btn-sm delete-product" data-product-id="{{ product.pk }}">Delete</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <th colspan="7" class="text-right">Raw Total:</th>
                <th id="raw-total">{{ view.object.raw_amount|space_thousands }}</th>
            </tr>
            <tr>
                <th colspan="7" class="text-right">Total Tax Amount:</th>
                <th id="tax-total">{{ view.object.total_tax_amount|space_thousands }}</th>
            </tr>
            <tr>
                <th colspan="7" class="text-right text-primary">Total Amount (Including Tax):</th>
                <th id="total-amount">{{ view.object.total_amount|space_thousands }}</th>
            </tr>
        </tfoot>
    </table>
    <!-- Accounting Summary -->
    <h3 class="mt-4">Accounting Summary</h3>
    <table class="table table-hover table-bordered mt-2 accounting-table">
        <thead class="thead-dark">
            <tr>
                <th class="align-middle">Date</th>
                <th class="align-middle label-column">Label</th>
                <th class="text-right align-middle">Debit</th>
                <th class="text-right align-middle">Credit</th>
                <th class="align-middle">Account Code</th>
                <th class="align-middle">Reference</th>
                <th class="align-middle">Journal</th>
                <th class="align-middle">Counterpart</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in view.object.get_accounting_entries %}
            <tr class="{% if entry.credit %}total-row font-weight-bold{% elif 'VAT' in entry.label %}vat-row{% endif %}">
                <td>{{ entry.date|date:"Y-m-d" }}</td>
                <td>{{ entry.label }}</td>
                <td class="text-right">
                    {% if entry.debit %}
                        {{ entry.debit|space_thousands }}
                    {% endif %}
                </td>
                <td class="text-right">
                    {% if entry.credit %}
                        {{ entry.credit|space_thousands }}
                    {% endif %}
                </td>
                <td>{{ entry.account_code }}</td>
                <td>{{ entry.reference }}</td>
                <td class="text-center">{{ entry.journal }}</td>
                <td>{{ entry.counterpart }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot class="bg-light">
            <tr class="font-weight-bold">
                <td colspan="2" class="text-right">Totals:</td>
                <td class="text-right">
                    {% with entries=view.object.get_accounting_entries %}
                        {{ entries|sum_debit|space_thousands }}
                    {% endwith %}
                </td>
                <td class="text-right">
                    {% with entries=view.object.get_accounting_entries %}
                        {{ entries|sum_credit|space_thousands }}
                    {% endwith %}
                </td>
                <td colspan="4"></td>
            </tr>
        </tfoot>
    </table>
{% else %}
    <div class="alert alert-warning mt-4">
        Save the invoice before adding products.
    </div>
{% endif %}

<!-- Modal Template for Adding Product -->
<div class="modal fade" id="productModal" tabindex="-1" role="dialog" aria-labelledby="productModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="productModalLabel">Add Product to Invoice</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <div id="modal-alert" class="alert d-none" role="alert"></div>
                <form id="add-product-form">
                    <div class="form-group">
                        <label for="product">Product:</label>
                        <input type="text" id="product" name="product" class="form-control" placeholder="Search for a product...">
                        <input type="hidden" id="product_id" name="product_id">
                        
                        <div id="new-product-fields" style="display: none;">
                            <input type="text" id="new-product-name" class="form-control mt-2" placeholder="New Product Name">
                            <input type="text" id="fiscal-label" class="form-control mt-2" placeholder="Fiscal Label">
                            <div class="custom-control custom-checkbox mt-2">
                                <input type="checkbox" class="custom-control-input" id="is-energy">
                                <label class="custom-control-label" for="is-energy">Is Energy Product</label>
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="expense_code">Expense Code:</label>
                        <input type="text" id="expense_code" name="expense_code" class="form-control" pattern="[0-9]{5,}" title="Expense code must be numeric and at least 5 characters long">
                    </div>
                    <div class="form-group">
                        <label for="quantity">Quantity:</label>
                        <input type="number" id="quantity" name="quantity" class="form-control" min="1">
                        <div class="invalid-feedback">
                            Please enter a valid quantity (minimum of 1).
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="unit_price">Unit Price:</label>
                        <input type="number" id="unit_price" name="unit_price" class="form-control" min="0.01" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="reduction_rate">Reduction Rate (%)</label>
                        <input type="number" id="reduction_rate" name="reduction_rate" class="form-control" min="0" max="100" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="vat_rate">VAT Rate (%):</label>
                        <select id="vat_rate" name="vat_rate" class="form-control">
                            <option value="0.00">0%</option>
                            <option value="7.00">7%</option>
                            <option value="10.00">10%</option>
                            <option value="11.00">11%</option>
                            <option value="14.00">14%</option>
                            <option value="16.00">16%</option>
                            <option value="20.00">20%</option>
                        </select>
                    </div>
                </form>
             </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" id="save-product-button" class="btn btn-primary">Save Product</button>
            </div>
        </div>
    </div>
</div>

<style>
    .ui-autocomplete {
        position: absolute;
        z-index: 2000;
        background-color: white;
        border: 1px solid #ccc;
        max-height: 200px;
        overflow-y: auto;
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .ui-menu-item {
        padding: 8px 12px;
        cursor: pointer;
    }
    
    .ui-menu-item:hover {
        background-color: #f8f9fa;
    }
</style>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        $('#productModal').on('hidden.bs.modal', function () {
        // Reset the form fields
        $('#add-product-form')[0].reset();

        // Remove validation styles
        $('#add-product-form .is-invalid').removeClass('is-invalid');

        // Remove error messages
        $('#add-product-form .invalid-feedback').remove();
    });

        $(document).ready(function() {
            $("#product").autocomplete({
            minLength: 2,
            source: function(request, response) {
                $.ajax({
                    url: "{% url 'product-autocomplete' %}",
                    dataType: "json",
                    data: { term: request.term },
                    success: function(data) {
                        response(data);
                    }
                });
            },

            select: function(event, ui) {
                $("#product").val(ui.item.label.split(' (')[0]);
                $("#product_id").val(ui.item.value);
                
                if (ui.item.value === 'new') {
                    $('#new-product-fields').show();
                    $('#expense_code').val('').prop('disabled', false);
                } else {
                    $('#new-product-fields').hide();
                    loadProductDetails(ui.item.value);
                }
                return false;
            }
        });
        
        // Test if element exists
        console.log("Product input element:", $("#product").length);
    });


        // Add this function to load product details
        function loadProductDetails(productId) {
            $.ajax({
                url: `/testapp/products/${productId}/details/`,  // You'll need to create this endpoint
                method: 'GET',
                success: function(data) {
                    $('#expense_code').val(data.expense_code).prop('disabled', true);
                    $('#vat_rate').val(data.vat_rate);
                },
                error: function() {
                    alert("Failed to load product details.");
                }
            });
}
        // Function to load products into dropdown
        function loadProducts(selectedProductId = null) {
        $.ajax({
            url: "{% url 'product-autocomplete' %}",
            method: "GET",
            success: function (data) {
                const productSelect = document.getElementById('product');
                productSelect.innerHTML = '<option value="">Select a Product</option>';
                productSelect.innerHTML += '<option value="new">+ Create New Product</option>';

                // Populate dropdown with products
                data.forEach(function (product) {
                    const option = document.createElement('option');
                    option.value = product.value;
                    option.text = product.label;
                    productSelect.appendChild(option);
                });

                // If a product ID is provided, select it
                if (selectedProductId) {
                    $('#product').val(selectedProductId);
                    $('#product').prop('disabled', true);
                    $('#new-product-fields').hide();
                } else {
                    $('#product').prop('disabled', false);
                }
            },
            error: function () {
                alert("Failed to load products.");
            }
        });
    }

        // Modal show event handler
        $('#productModal').on('show.bs.modal', function () {
            const editingProductId = $('#save-product-button').attr('data-editing');
            if (!editingProductId) {
                // Add mode - load all products
                loadProducts();
            }
        });

        // Save button click handler
        document.getElementById('save-product-button').addEventListener('click', function () {
            const productId = $('#save-product-button').attr('data-editing');
            const selectedProductId = $('#product_id').val();
            const quantity = $('#quantity').val();
            const unitPrice = $('#unit_price').val();
            const reductionRate = $('#reduction_rate').val();
            const vatRate = $('#vat_rate').val();
            const expenseCode = $('#expense_code').val();
            const isNewProduct = selectedProductId === 'new';

            // Validate fields before submission
            let isValid = true;
            let errorMessage = "";

            if (!productId && !selectedProductId) {  // Only validate product selection in add mode
                isValid = false;
                errorMessage += "Please select a product.\n";
            }
            if (quantity <= 0) {
                isValid = false;
                errorMessage += "Quantity must be a positive number.\n";
            }
            if (unitPrice <= 0) {
                isValid = false;
                errorMessage += "Unit Price must be a positive value.\n";
            }
            if (reductionRate < 0 || reductionRate > 100) {
                isValid = false;
                errorMessage += "Reduction Rate must be between 0 and 100.\n";
            }
            if (!/^\d{5,}$/.test(expenseCode)) {
                isValid = false;
                errorMessage += "Expense code must be numeric and at least 5 characters long.\n";
            }

            if (isNewProduct) {
                if (!$('#new-product-name').val()) {
                    isValid = false;
                    errorMessage += "Product name is required.\n";
                }
                if (!$('#fiscal-label').val()) {
                    isValid = false;
                    errorMessage += "Fiscal label is required.\n";
                }
            }

            if (!isValid) {
                alert(errorMessage);
                return;
            }

            // If creating a new product
            if (isNewProduct && !productId) {
                // First create the product
                const productData = {
                    name: $('#new-product-name').val(),
                    fiscal_label: $('#fiscal-label').val(),
                    is_energy: $('#is-energy').is(':checked'),
                    expense_code: expenseCode,
                    vat_rate: vatRate,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                };

                $.ajax({
                    url: "{% url 'product-ajax-create' %}",
                    method: "POST",
                    data: productData,
                    success: function(response) {
                        // Now create the invoice product with the new product ID
                        const requestData = {
                            quantity: quantity,
                            unit_price: unitPrice,
                            reduction_rate: reductionRate,
                            vat_rate: vatRate,
                            expense_code: expenseCode,
                            invoice_id: '{{ view.object.pk }}',
                            product: response.product_id,
                            csrfmiddlewaretoken: '{{ csrf_token }}'
                        };

                        $.ajax({
                            url: "{% url 'add-product-to-invoice' %}",
                            method: "POST",
                            data: requestData,
                            success: function(response) {
                                location.reload();
                            },
                            error: function(error) {
                                alert("Failed to add product to invoice.");
                                console.error(error);
                            }
                        });
                    },
                    error: function(error) {
                        alert("Failed to create new product.");
                        console.error(error);
                    }
                });
            } else {
                // Existing logic for editing or adding existing product
                const requestData = {
                    quantity: quantity,
                    unit_price: unitPrice,
                    reduction_rate: reductionRate,
                    vat_rate: vatRate,
                    expense_code: expenseCode,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                };

                if (!productId) {
                    // Add mode - include additional fields
                    requestData.invoice_id = '{{ view.object.pk }}';
                    requestData.product = selectedProductId;
                }

                // Make AJAX request
                $.ajax({
                    url: productId ? 
                        `/testapp/invoices/edit-product/${productId}/` : 
                        "{% url 'add-product-to-invoice' %}",
                    method: "POST",
                    data: requestData,
                    success: function (response) {
                        location.reload();
                    },
                    error: function (error) {
                        alert("Failed to save product. Please try again.");
                        console.error(error);
                    }
                });
            }
        });

        // Edit button click handler
        document.querySelectorAll('.edit-product').forEach(function (editButton) {
            editButton.addEventListener('click', function () {
                const productId = editButton.getAttribute('data-product-id');

                // Load product data into the modal for editing
                $.ajax({
                    url: `/testapp/invoices/edit-product/${productId}/`,
                    method: "GET",
                    success: function (data) {
                        // First load all products, then set the selected one
                        loadProducts(data.product);
                        
                        // Populate other fields
                        $('#product').val(data.product_name); // Add product_name to your EditProductInInvoiceView response
                        $('#product_id').val(data.product);
                        $('#productModalLabel').text('Edit Product in Invoice');
                        $('#quantity').val(data.quantity);
                        $('#unit_price').val(data.unit_price);
                        $('#reduction_rate').val(data.reduction_rate);
                        $('#vat_rate').val(data.vat_rate.toFixed(2)).prop('disabled', true);
                        $('#expense_code').val(data.expense_code).prop('disabled', true);

                        // Set editing mode
                        $('#save-product-button').attr('data-editing', productId);
                        $('#productModal').modal('show');
                    },
                    error: function (error) {
                        alert("Failed to load product data for editing.");
                    }
                });
            });
        });

        // Delete button click handler
        document.querySelectorAll('.delete-product').forEach(function (deleteButton) {
            deleteButton.addEventListener('click', function () {
                const productId = deleteButton.getAttribute('data-product-id');

                if (confirm("Are you sure you want to delete this product?")) {
                    $.ajax({
                        url: `/testapp/invoices/edit-product/${productId}/`,
                        method: "DELETE",
                        headers: {
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        success: function (response) {
                            deleteButton.closest('tr').remove();
                        },
                        error: function (error) {
                            alert("Failed to delete product. Please try again.");
                        }
                    });
                }
            });
        });

        // Modal close handler
        $('#productModal').on('hidden.bs.modal', function () {
            $('#add-product-form')[0].reset();
            $('#save-product-button').removeAttr('data-editing');
            $('#productModalLabel').text('Add Product to Invoice');
            $('#product').prop('disabled', false);  // Re-enable product selection
            $('#new-product-fields').hide(); // Hide new product fields
            $('#expense_code').prop('disabled', false); // Reset expense code field
        });

        const form = document.getElementById("add-product-form");
        const alertBox = document.getElementById("modal-alert");

        document.getElementById("save-product-button").addEventListener("click", () => {
            // Clear previous alerts
            alertBox.classList.add("d-none");
            alertBox.innerHTML = "";

            // Reset validation states
            const inputs = form.querySelectorAll(".form-control");
            inputs.forEach((input) => {
                input.classList.remove("is-invalid");
            });

            // Validate fields
            let isValid = true;

            // Example validation: Quantity
            const quantity = document.getElementById("quantity");
            if (!quantity.value || quantity.value < 1) {
                isValid = false;
                quantity.classList.add("is-invalid");
                quantity.nextElementSibling.textContent = "Quantity must be at least 1.";
            }

            // Example validation: Expense Code
            const expenseCode = document.getElementById("expense_code");
            if (!quantity.value ||!/^[0-9]{5,}$/.test(expenseCode.value)) {
                isValid = false;
                expenseCode.classList.add("is-invalid");
                expenseCode.nextElementSibling.textContent =
                    "Expense code must be numeric and at least 5 characters long.";
            }

            if (isValid) {
                // Simulate form submission success
                alertBox.className = "alert alert-success";
                alertBox.textContent = "Product saved successfully!";
                alertBox.classList.remove("d-none");

                // Close modal after 2 seconds
                setTimeout(() => {
                    $("#productModal").modal("hide");
                }, 2000);
            } else {
                // Show error alert
                alertBox.className = "alert alert-danger";
                alertBox.textContent = "Please fix the errors in the form.";
                alertBox.classList.remove("d-none");
            }
        });
    });
</script>
{% endblock %}

```

# testapp/templates/invoice/invoice_list.html

```html
{% extends 'base.html' %}
{% load humanize %}

{% block title %}Invoice List{% endblock %}

{% block content %}
<h1>Invoice List</h1>
<a href="{% url 'invoice-create' %}" class="btn btn-primary">Add New Invoice</a>

<table class="table mt-4">
    <thead>
        <tr>
            <th>Export</th>
            <th>Date</th>
            <th>Reference</th>
            <th>Supplier</th>
            <th>Fiscal Label</th>
            <th>Raw Amount</th>
            <th>Tax Rate (%)</th>
            <th>Tax Amount</th>
            <th>Total Amount (Incl. Tax)</th>
            <th>Status</th>
            <th>Actions</th>
            <th>Details</th>
        </tr>
    </thead>
    <tbody>
        {% for invoice in invoices %}
            <tr {% if invoice.exported_at %}class="table-light"{% endif %}>
                <td>
                    {% if invoice.exported_at %}
                        <span class="text-muted">
                            Exported {{ invoice.exported_at|date:"d-m-Y" }}
                            <button type="button" 
                                    class="btn btn-warning btn-sm unexport-btn ml-2" 
                                    data-invoice-id="{{ invoice.id }}">
                                <i class="fas fa-undo"></i>
                            </button>
                        </span>
                    {% else %}
                        <input type="checkbox" 
                            name="invoice_ids" 
                            value="{{ invoice.id }}" 
                            class="export-checkbox">
                    {% endif %}
                </td>
                <td>{{ invoice.date }}</td>
                <td>{{ invoice.ref }}</td>
                <td>{{ invoice.supplier.name }}</td>
                <td>{{ invoice.fiscal_label }}</td>
                <td>{{ invoice.raw_amount|floatformat:2|intcomma }}</td>
                <td>
                    {% with invoice.products.all|length as product_count %}
                        {% for product in invoice.products.all %}
                            {{ product.vat_rate }}{% if not forloop.last %}, {% endif %}
                        {% endfor %}
                    {% endwith %}
                </td>
                <td>
                    {% if invoice.total_tax_amount %}
                        {{ invoice.total_tax_amount|floatformat:2|intcomma }}
                    {% else %}
                        <strong>Tax Missing</strong>
                    {% endif %}
                </td>                
                <td>{{ invoice.total_amount|floatformat:2|intcomma }}</td>
                <td>
                    {% if invoice.payment_status == 'paid' %}
                        <span class="badge badge-success">Paid</span>
                    {% elif invoice.payment_status == 'partially_paid' %}
                        <span class="badge badge-warning">
                            Partially Paid 
                            <small>({{ invoice.payments_summary.percentage_paid|floatformat:1 }}%)</small>
                        </span>
                    {% else %}
                        <span class="badge badge-danger">Not Paid</span>
                    {% endif %}
                </td>
                <td>
                    <a href="{% url 'invoice-update' invoice.pk %}" class="btn btn-warning">Edit</a>
                    <a href="{% url 'invoice-delete' invoice.pk %}" class="btn btn-danger">Delete</a>
                </td>
                <td>
                    <button class="btn btn-info" data-toggle="modal" data-target="#invoiceDetailsModal" data-invoice="{{ invoice.pk }}">Details</button>
                    <button class="btn btn-info btn-sm"                             
                            data-toggle="modal" 
                            data-target="#paymentDetailsModal"
                            data-invoice="{{ invoice.pk }}">
                        Payment Details
                    </button>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="10">No invoices found.</td>
            </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Export Button -->
<div class="d-flex justify-content-end mt-3">
    <button type="button" 
            id="export-selected" 
            class="btn btn-primary" 
            disabled>
        Export Selected
    </button>
</div>

<!-- Modal Template -->
<div class="modal fade" id="invoiceDetailsModal" tabindex="-1" role="dialog" aria-labelledby="invoiceDetailsModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document"> <!-- Added modal-lg for larger modal -->
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="invoiceDetailsModalLabel">Invoice Details</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body modal-scrollable-content">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Unit Price</th>
                            <th>Quantity</th>
                            <th>VAT Rate</th>
                            <th>Reduction Rate</th>
                            <th>Raw Price</th>
                        </tr>
                    </thead>
                    <tbody id="invoice-details-table">
                        <!-- Filled by JavaScript -->
                    </tbody>
                </table>
                <div id="vat-summary"></div>
                <div id="total-amount-summary"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- Payment Details Modal -->
<div class="modal fade" id="paymentDetailsModal">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Payment Details</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <!-- Summary Cards -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Due</h6>
                                <h4 id="amount-due" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Paid</h6>
                                <h4 id="amount-paid" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount to Issue</h6>
                                <h4 id="amount-to-issue" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="progress mb-4" style="height: 25px;">
                    <div id="payment-progress" 
                         class="progress-bar" 
                         role="progressbar" 
                         style="width: 0%"></div>
                </div>

                <!-- Detailed Breakdown -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <p class="mb-1">Pending Payments:</p>
                        <h5 id="pending-amount"></h5>
                    </div>
                    <div class="col-md-4">
                        <p class="mb-1">Delivered Payments:</p>
                        <h5 id="delivered-amount"></h5>
                    </div>
                    <div class="col-md-4">
                        <p class="mb-1">Remaining to Pay:</p>
                        <h5 id="remaining-amount"></h5>
                    </div>
                </div>

                <!-- Checks Table -->
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Reference</th>
                                <th>Amount</th>
                                <th>Created</th>
                                <th>Delivered</th>
                                <th>Paid</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="payment-checks-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- JavaScript to populate modal -->
<script>
    document.addEventListener('DOMContentLoaded', function () {
        // Export functionality
        const checkboxes = document.querySelectorAll('.export-checkbox');
        const exportButton = document.getElementById('export-selected');

        checkboxes.forEach(function(checkbox) {
            checkbox.addEventListener('click', function() {
                const checkedBoxes = document.querySelectorAll('.export-checkbox:checked');
                exportButton.disabled = checkedBoxes.length === 0;
                console.log('Checked boxes:', checkedBoxes.length);
            });
        });

        exportButton.addEventListener('click', function() {
            const selectedIds = [...checkboxes]
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            if (selectedIds.length === 0) return;

            fetch('{% url "export-invoices" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({invoice_ids: selectedIds})
            })
            .then(response => {
                if (response.ok) return response.blob();
                throw new Error('Export failed');
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `accounting_export_${new Date().toISOString().slice(0,19).replace(/[:-]/g, '')}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                location.reload();
            })
            .catch(error => {
                alert('Failed to export invoices: ' + error.message);
            });
        });

        // Unexport functionality
        const unexportButtons = document.querySelectorAll('.unexport-btn');
        unexportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const invoiceId = this.dataset.invoiceId;
                if (!confirm('Are you sure you want to unexport this invoice?')) return;

                fetch(`/testapp/invoices/${invoiceId}/unexport/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) throw new Error('Unexport failed');
                    location.reload();
                })
                .catch(error => {
                    alert('Failed to unexport invoice: ' + error.message);
                });
            });
        });

        // Payment details functionality
        $('#paymentDetailsModal').on('show.bs.modal', function (event) {
            const button = $(event.relatedTarget); // Button that triggered the modal
            const invoiceId = button.data('invoice'); // Extract invoice ID

            // Fetch payment details via AJAX
            $.get(`/testapp/invoices/${invoiceId}/payment-details/`, function (data) {
                const details = data.payment_details;

                // Update summary section
                $('#amount-due').text(formatMoney(details.total_amount));
                $('#amount-paid').text(formatMoney(details.paid_amount));
                $('#amount-to-issue').text(formatMoney(details.amount_to_issue));

                // Update progress bar
                const progressBar = $('#payment-progress');
                progressBar
                    .css('width', `${details.payment_percentage}%`)
                    .text(`${details.payment_percentage.toFixed(1)}%`)
                    .removeClass('bg-success bg-warning bg-danger')
                    .addClass(getProgressBarClass(details.payment_percentage));

                // Update detailed breakdown
                $('#pending-amount').text(formatMoney(details.pending_amount));
                $('#delivered-amount').text(formatMoney(details.delivered_amount));
                $('#remaining-amount').text(formatMoney(details.remaining_to_pay));

                // Update checks table
                updateChecksTable(data.checks);
            });
        });

        // Utility function to format money
        function formatMoney(amount) {
            return new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'MAD',
                minimumFractionDigits: 2
            }).format(amount);
        }

        // Utility function to get progress bar class
        function getProgressBarClass(percentage) {
            if (percentage >= 100) return 'bg-success';
            if (percentage > 50) return 'bg-warning';
            return 'bg-danger';
        }

        // Update checks table with data
        function updateChecksTable(checks) {
            const tbody = $('#payment-checks-tbody');
            tbody.empty();

            checks.forEach(check => {
                tbody.append(`
                    <tr>
                        <td>${check.reference}</td>
                        <td>${formatMoney(check.amount)}</td>
                        <td>${check.created_at}</td>
                        <td>${check.delivered_at || '-'}</td>
                        <td>${check.paid_at || '-'}</td>
                        <td>
                            <span class="badge badge-${getStatusBadgeClass(check.status)}">
                                ${formatStatus(check.status)}
                            </span>
                        </td>
                    </tr>
                `);
            });
        }

        // Utility function to get badge class for status
        function getStatusBadgeClass(status) {
            return {
                'pending': 'secondary',
                'delivered': 'warning',
                'paid': 'success',
                'cancelled': 'danger'
            }[status] || 'secondary';
        }

        // Utility function to format status text
        function formatStatus(status) {
            return status.charAt(0).toUpperCase() + status.slice(1);
        }



        // Invoice details functionality
        $('#invoiceDetailsModal').on('show.bs.modal', function (event) {
            const button = $(event.relatedTarget);
            const invoiceId = button.data('invoice');

            $.ajax({
                url: "{% url 'invoice-details' %}",
                data: {
                    'invoice_id': invoiceId
                },
                success: function (data) {
                    // Populate the modal with the invoice details
                    $('#invoice-details-table').empty();
                    data.products.forEach(product => {
                        $('#invoice-details-table').append(`
                            <tr>
                                <td>${product.name}</td>
                                <td>${product.unit_price}</td>
                                <td>${product.quantity}</td>
                                <td>${product.vat_rate}</td> <!-- VAT Rate -->
                                <td>${product.reduction_rate}</td>
                                <td>${product.raw_price}</td>
                            </tr>
                        `);
                    });
                    
                    // Update the VAT summary, Total Raw Amount, and Total Amount
                    $('#vat-summary').empty();
                    data.vat_subtotals.forEach(vatSubtotal => {
                        $('#vat-summary').append(`<p><strong>Subtotal for VAT ${vatSubtotal.vat_rate}:</strong> ${vatSubtotal.subtotal}</p>`);
                    });
                    
                    $('#total-amount-summary').html(`
                    <strong>Total Raw Amount:</strong> ${data.total_raw_amount}<br>
                    <strong>Total VAT Amount:</strong> ${data.total_vat}<br>
                    <strong>Total Amount (Including Tax):</strong> ${data.total_amount}
                    `);
                }
            });
        });
        const productFormsDiv = document.getElementById('product-forms');
        const addProductButton = document.getElementById('add-product');
        let totalFormsInput = document.querySelector('#id_products-TOTAL_FORMS');
        let formIndex = parseInt(totalFormsInput.value);  // Start with the current total number of forms

        // Add product form when clicking 'Add Product'
        addProductButton.addEventListener('click', function() {
            const newForm = productFormsDiv.querySelector('.product-form').cloneNode(true);
            newForm.querySelectorAll('input').forEach(input => input.value = '');
            newForm.innerHTML = newForm.innerHTML.replace(/products-(\d+)-/g, `products-${formIndex}-`);
            formIndex++;
            totalFormsInput.value = formIndex;  // Update TOTAL_FORMS count

            productFormsDiv.appendChild(newForm);
            addAutocomplete(newForm);  // Add autocomplete for the newly added product form

            newForm.querySelector('.remove-product').addEventListener('click', function() {
                newForm.remove();
                updateTotalFormsCount();
            });
        });

        // Remove product form when clicking 'Remove Product'
        document.querySelectorAll('.remove-product').forEach(button => {
            button.addEventListener('click', function() {
                button.parentElement.remove();
                updateTotalFormsCount();
            });
        });

        // Update TOTAL_FORMS count
        function updateTotalFormsCount() {
            formIndex = productFormsDiv.querySelectorAll('.product-form').length;
            totalFormsInput.value = formIndex;
        }

        // Add jQuery autocomplete to all product name fields
        function addAutocomplete(formElement) {
            $(formElement).find('input[name$="-product"]').autocomplete({
                source: function(request, response) {
                    $.ajax({
                        url: "{% url 'product-autocomplete' %}",
                        data: {
                            term: request.term
                        },
                        success: function(data) {
                            response(data);
                        }
                    });
                },
                minLength: 2,
                select: function(event, ui) {
                    const productInput = event.target;
                    const formPrefix = productInput.name.split('-').slice(0, -1).join('-');
                    $(`input[name="${formPrefix}-expense_code"]`).val(ui.item.expense_code);
                    $(`input[name="${formPrefix}-vat_rate"]`).val(ui.item.vat_rate);
                    $(`input[name="${formPrefix}-fiscal_label"]`).val(ui.item.fiscal_label);
                }
            });
        }

         
        // Initialize autocomplete for existing forms
        document.querySelectorAll('.product-form').forEach(addAutocomplete);

       
    });
</script>

{% endblock %}

```

# testapp/templates/login.html

```html
{% extends 'base.html' %}

{% block title %}Login - MyProject{% endblock %}

{% block content %}
<div class="container">
    <h2>Login</h2>
    <form method="post">
        {% csrf_token %}
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary">Login</button>
    </form>
</div>
{% endblock %}

```

# testapp/templates/product/product_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Product{% endblock %}

{% block content %}
<h1>Delete Product</h1>
<p>Are you sure you want to delete "{{ product.name }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/product/product_form.html

```html
{% extends 'base.html' %}

{% block title %}Product Form{% endblock %}

{% block content %}
<h1>{{ view.object.name|default:'Add New Product' }}</h1>
<form method="post">
    {% csrf_token %}
    {% for field in form %}
        {% if field.name == 'vat_rate' %}
            <div class="form-group">
                <label>{{ field.label }}</label>
                <select name="{{ field.name }}" class="form-control auto-size-select">
                    {% for choice in field.field.choices %}
                        <option value="{{ choice.0 }}" {% if field.value|floatformat:2 == choice.0|floatformat:2 %}selected{% endif %}>
                            {{ choice.1 }}
                        </option>
                    {% endfor %}
                </select>
            </div>
        {% else %}
            <div class="form-group">
                {{ field.label_tag }}
                {{ field }}
            </div>
        {% endif %}
    {% endfor %}
    <button type="submit" class="btn btn-success">Save</button>
    <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a>
</form>

<style>
    .auto-size-select {
        display: inline-block;
        min-width: 100px; /* Set a reasonable minimum width */
        max-width: 100%; /* Ensure it doesn't exceed the container width */
        width: auto; /* Automatically adjust to content */
    }
</style>

<script>
    document.querySelectorAll('.auto-size-select').forEach(select => {
        select.style.width = `${select.scrollWidth}px`;
    });
</script>


{% endblock %}

```

# testapp/templates/product/product_list.html

```html
{% extends 'base.html' %}

{% block title %}Product List{% endblock %}

{% block content %}
<h1>Product List</h1>
<a href="{% url 'product-create' %}" class="btn btn-primary">Add New Product</a>
<table class="table mt-4">
    <thead>
        <tr>
            <th>Name</th>
            <th>VAT Rate</th>
            <th>Expense Code</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for product in products %}
            <tr>
                <td>{{ product.name }}</td>
                <td>{{ product.vat_rate }}</td>
                <td>{{ product.expense_code }}</td>
                <td>
                    <a href="{% url 'product-update' product.pk %}" class="btn btn-warning">Edit</a>
                    <a href="{% url 'product-delete' product.pk %}" class="btn btn-danger">Delete</a>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="4">No products found.</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}

```

# testapp/templates/profile.html

```html
{% extends 'base.html' %}

{% block title %}Profile{% endblock %}

{% block content %}
    <h1>Profile Page</h1>
    <p>First Name: {{ user.first_name }}</p>
    <p>Last Name: {{ user.last_name }}</p>
    <p>Email: {{ user.email }}</p>
{% endblock %}

```

# testapp/templates/supplier/supplier_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Supplier{% endblock %}

{% block content %}
<h1>Delete Supplier</h1>
<p>Are you sure you want to delete "{{ supplier.name }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/supplier/supplier_form.html

```html
{% extends 'base.html' %}

{% block title %}Supplier Form{% endblock %}

{% block content %}
<h1>{{ view.object.pk|default:'Add New Supplier' }}</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-success">Save</button>
    <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/supplier/supplier_list.html

```html
{% extends 'base.html' %}

{% block title %}Supplier List{% endblock %}

{% block content %}
<h1>Supplier List</h1>
<a href="{% url 'supplier-create' %}" class="btn btn-primary">Add New Supplier</a>
<table class="table mt-4">
    <thead>
        <tr>
            <th>Name</th>
            <th>IF Code</th>
            <th>ICE Code</th>
            <th>RC Code</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for supplier in suppliers %}
            <tr>
                <td>{{ supplier.name }}</td>
                <td>{{ supplier.if_code }}</td>
                <td>{{ supplier.ice_code }}</td>
                <td>{{ supplier.rc_code }}</td>
                <td>
                    <a href="{% url 'supplier-update' supplier.pk %}" class="btn btn-warning">Edit</a>
                    <a href="{% url 'supplier-delete' supplier.pk %}" class="btn btn-danger">Delete</a>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="5">No suppliers found.</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}

```

# testapp/templatetags/__init__.py

```py

```

# testapp/templatetags/accounting_filters.py

```py
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def sum_debit(entries):
    return sum(entry['debit'] or 0 for entry in entries)

@register.filter
def sum_credit(entries):
    return sum(entry['credit'] or 0 for entry in entries)

@register.filter
def space_thousands(value):
    """
    Formats a number with spaces as thousand separators and 2 decimal places
    Example: 1234567.89 becomes 1 234 567.89
    """
    if value is None:
        return ''
    
    # Format to 2 decimal places first
    formatted = floatformat(value, 2)
    
    # Split the number into integer and decimal parts
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
    else:
        integer_part, decimal_part = formatted, '00'

    # Add space thousand separators to integer part
    int_with_spaces = ''
    for i, digit in enumerate(reversed(integer_part)):
        if i and i % 3 == 0:
            int_with_spaces = ' ' + int_with_spaces
        int_with_spaces = digit + int_with_spaces

    return f'{int_with_spaces}.{decimal_part}'
```

# testapp/templatetags/check_tags.py

```py
from django import template

register = template.Library()

@register.filter
def status_badge(status):
    return {
        'pending': 'secondary',
        'delivered': 'warning',
        'paid': 'success',
        'cancelled': 'danger'
    }.get(status, 'secondary')
```

# testapp/tests.py

```py
from django.test import TestCase

# Create your tests here.

```

# testapp/urls.py

```py
from django.urls import path
from . import views
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView
from .views_product import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductAjaxCreateView, ProductDetailsView
from .views_invoice import (
    InvoiceListView, InvoiceCreateView, InvoiceUpdateView, InvoiceDeleteView, InvoiceDetailsView,
    product_autocomplete, AddProductToInvoiceView, EditProductInInvoiceView, ExportInvoicesView, UnexportInvoiceView,
    InvoicePaymentDetailsView  # Import the EditProductInInvoiceView
)
from .views_checkers import (
    CheckerListView, CheckerCreateView, CheckerDetailsView, CheckCreateView, CheckListView, CheckStatusView,
    invoice_autocomplete, supplier_autocomplete, CheckerDeleteView, CheckUpdateView, CheckCancelView
)

urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view

    # Supplier CRUD operations
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),  # List all suppliers
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier-create'),  # Create a new supplier
    path('suppliers/<uuid:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),  # Update a supplier
    path('suppliers/<uuid:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),  # Delete a supplier

    # Product CRUD operations
    path('products/', ProductListView.as_view(), name='product-list'),  # List all products
    path('products/create/', ProductCreateView.as_view(), name='product-create'),  # Create a new product
    path('products/<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),  # Update a product
    path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),  # Delete a product
    path('products/<uuid:pk>/details/', ProductDetailsView.as_view(), name='product-details'),  # Details for a specific product
    path('products/ajax-create/', ProductAjaxCreateView.as_view(), name='product-ajax-create'),  # AJAX view for creating a new Product

    # Invoice CRUD operations
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),  # List all invoices
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),  # Create a new invoice
    path('invoices/<uuid:pk>/update/', InvoiceUpdateView.as_view(), name='invoice-update'),  # Update an invoice
    path('invoices/<uuid:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice-delete'),  # Delete an invoice
    path('products/autocomplete/', product_autocomplete, name='product-autocomplete'),  # Autocomplete for products
    path('invoices/details/', InvoiceDetailsView.as_view(), name='invoice-details'),  # Details for a specific invoice
    path('invoices/add-product/', AddProductToInvoiceView.as_view(), name='add-product-to-invoice'),  # Add a product to an invoice
    path('invoices/edit-product/<uuid:pk>/', EditProductInInvoiceView.as_view(), name='invoice-edit-product'),  # Edit a product in an invoice
    path('invoices/export/', ExportInvoicesView.as_view(), name='export-invoices'),
    path('invoices/<uuid:invoice_id>/unexport/', UnexportInvoiceView.as_view(), name='unexport-invoice'),
    path('invoices/<str:pk>/payment-details/', InvoicePaymentDetailsView.as_view(), name='invoice-payment-details'),

    path('suppliers/autocomplete/', supplier_autocomplete, name='supplier-autocomplete'),  # Autocomplete for suppliers
    path('checkers/', CheckerListView.as_view(), name='checker-list'),  # List all checkers
    path('checkers/create/', CheckerCreateView.as_view(), name='checker-create'),
    path('checkers/<uuid:pk>/details/', CheckerDetailsView.as_view(), name='checker-details'),
    path('checkers/<uuid:pk>/delete/', CheckerDeleteView.as_view(), name='checker-delete'),
    path('checks/create/', CheckCreateView.as_view(), name='check-create'),
    path('checks/', CheckListView.as_view(), name='check-list'),
    path('checks/<uuid:pk>/mark-delivered/', 
        CheckStatusView.as_view(), {'action': 'delivered'}, name='check-mark-delivered'),
    path('checks/<uuid:pk>/mark-paid/', 
        CheckStatusView.as_view(), {'action': 'paid'}, name='check-mark-paid'),
    path('invoices/autocomplete/', invoice_autocomplete, name='invoice-autocomplete'),
    path('checks/<uuid:pk>/', CheckUpdateView.as_view(), name='check-update'),
    path('checks/<uuid:pk>/cancel/', CheckCancelView.as_view(), name='check-cancel'),

]

```

# testapp/views_checkers.py

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Checker, Check, Invoice, Supplier
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from dateutil.parser import parse


class CheckerListView(ListView):
    model = Checker
    template_name = 'checker/checker_list.html'
    context_object_name = 'checkers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = Checker.BANK_CHOICES
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CheckerCreateView(View):
        def post(self, request):
            try:
                print("Received data:", request.body)
                data = json.loads(request.body)
                print("Parsed data:", data)
                
                # Validate final page
                starting_page = int(data['starting_page'])
                num_pages = int(data['num_pages'])
                calculated_final = starting_page + num_pages - 1
                
                checker = Checker.objects.create(
                    type=data['type'],
                    bank=data['bank'],
                    account_number=data['account_number'],
                    city=data['city'],
                    num_pages=num_pages,
                    index=data['index'].upper(),
                    starting_page=starting_page,
                    final_page=calculated_final
                )
                
                return JsonResponse({
                    'message': 'Checker created successfully',
                    'checker_id': str(checker.id)
                })
                
            except Exception as e:
                print("Error:", e)
                return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckerDetailsView(View):
        def get(self, request, pk):
            try:
                checker = get_object_or_404(Checker, pk=pk)
                return JsonResponse({
                    'code': checker.code,
                    'type': checker.type,
                    'bank': checker.get_bank_display(),
                    'account_number': checker.account_number,
                    'city': checker.city,
                    'num_pages': checker.num_pages,
                    'index': checker.index,
                    'starting_page': checker.starting_page,
                    'final_page': checker.final_page,
                    'current_position': checker.current_position,
                    'remaining_pages': checker.final_page - checker.current_position + 1
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

class CheckerDeleteView(View):
    def post(self, request, pk):
        try:
            checker = get_object_or_404(Checker, pk=pk)
            if checker.checks.exists():
                return JsonResponse({'error': 'Cannot delete checker with existing checks'}, status=400)
            checker.delete()
            return JsonResponse({'message': 'Checker deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def invoice_autocomplete(request):
    query = request.GET.get('term', '')
    supplier_id = request.GET.get('supplier')
    print("Query:", query)  # Debug
    print("Supplier ID:", supplier_id)  # Debug
    
    invoices = Invoice.objects.filter(
        supplier_id=supplier_id,
        ref__icontains=query
    )
    print("Found invoices:", invoices.count())  # Debug
    print("Query SQL:", invoices.query)  # Debug
    
    invoice_list = [{
        'label': f"{i.ref} ({i.date}) - {i.total_amount:,.2f}",
        'value': str(i.id),
        'amount': float(i.total_amount)
    } for i in invoices]
    
    print("Response:", invoice_list)  # Debug
    return JsonResponse(invoice_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            invoice = get_object_or_404(Invoice, pk=data['invoice_id'])

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            
            check = Check.objects.create(
                checker=checker,
                creation_date=data.get('creation_date', timezone.now().date()),
                beneficiary=invoice.supplier,
                cause=invoice,
                payment_due=payment_due,
                amount_due=invoice.total_amount,
                amount=data['amount'],
                observation=data.get('observation', '')
            )
            
            return JsonResponse({
                'message': 'Check created successfully',
                'check_id': str(check.id)
            })
            
        except Exception as e:
            print("Error creating check:", str(e))  # Debug print
            return JsonResponse({'error': str(e)}, status=400)
    
class CheckListView(ListView):
    model = Check
    template_name = 'checker/check_list.html'
    context_object_name = 'checks'

    def get_queryset(self):
        return Check.objects.select_related('checker', 'beneficiary', 'cause')


@method_decorator(csrf_exempt, name='dispatch')
class CheckStatusView(View):
    def post(self, request, pk, action):
        try:
            check = get_object_or_404(Check, pk=pk)
            
            if action == 'delivered':
                if check.delivered:
                    return JsonResponse({'error': 'Check already delivered'}, status=400)
                check.delivered = True
            elif action == 'paid':
                if not check.delivered:
                    return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                if check.paid:
                    return JsonResponse({'error': 'Check already paid'}, status=400)
                check.paid = True
            
            check.save()
            return JsonResponse({'message': f'Check marked as {action}'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def supplier_autocomplete(request):
    query = request.GET.get('term', '')
    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) | 
        Q(accounting_code__icontains=query)
    )[:10]
    
    supplier_list = [{
        "label": f"{supplier.name} ({supplier.accounting_code})",
        "value": str(supplier.id)
    } for supplier in suppliers]
    
    return JsonResponse(supplier_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckUpdateView(View):
    def get(self, request, pk):
        try:
            check = get_object_or_404(Check, pk=pk)
            return JsonResponse({
                'id': str(check.id),
                'status': check.status,
                'delivered_at': check.delivered_at.strftime('%Y-%m-%dT%H:%M') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%dT%H:%M') if check.paid_at else None,
                'cancelled_at': check.cancelled_at.strftime('%Y-%m-%dT%H:%M') if check.cancelled_at else None,
                'cancellation_reason': check.cancellation_reason
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if 'delivered_at' in data:
                check.delivered_at = parse(data['delivered_at']) if data['delivered_at'] else None
                check.delivered = bool(check.delivered_at)
                if check.delivered_at:
                    check.status = 'delivered'
            
            if 'paid_at' in data:
                if data['paid_at'] and not check.delivered_at:
                    return JsonResponse({'error': 'Check must be delivered before being marked as paid'}, status=400)
                check.paid_at = parse(data['paid_at']) if data['paid_at'] else None
                check.paid = bool(check.paid_at)
                if check.paid_at:
                    check.status = 'paid'
            
            check.save()
            return JsonResponse({'message': 'Check updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class CheckCancelView(View):
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if check.paid_at:
                return JsonResponse({'error': 'Cannot cancel a paid check'}, status=400)
                
            check.cancelled_at = timezone.now()
            check.cancellation_reason = data.get('reason')
            check.status = 'cancelled'
            check.save()
            
            return JsonResponse({'message': 'Check cancelled successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
```

# testapp/views_invoice.py

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Invoice, InvoiceProduct, Product, ExportRecord, Check
from .forms import InvoiceCreateForm, InvoiceUpdateForm  # Import the custom form here
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages


@method_decorator(csrf_exempt, name='dispatch')
class AddProductToInvoiceView(View):
    def post(self, request):
        invoice_id = request.POST.get('invoice_id')
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate', 0)  # Add default value
        expense_code = request.POST.get('expense_code')

        try:
            # Fetch the invoice and product
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            product = get_object_or_404(Product, pk=product_id)

            # Create a new InvoiceProduct entry
            invoice_product = InvoiceProduct.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                vat_rate=vat_rate,
                reduction_rate=reduction_rate
            )

            # Success response
            return JsonResponse({"message": "Product added successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# List all Invoices
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice/invoice_list.html'
    context_object_name = 'invoices'

# Create a new Invoice
class InvoiceCreateView(SuccessMessageMixin, CreateView):
    model = Invoice
    form_class = InvoiceUpdateForm  # Use the custom form here
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully created."

    def form_valid(self, form):
        response = super().form_valid(form)
        # We may want to pass the newly created invoice to the next page or modal
        return response

    def get_form_class(self):
        print("Using CREATE VIEW")  # Debug print
        return InvoiceCreateForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()  # Add all products to the context for dropdown population
        return data

# Update an existing Invoice
class InvoiceUpdateView(SuccessMessageMixin, UpdateView):
    model = Invoice
    form_class = InvoiceUpdateForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully updated."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs) 
        if self.request.POST:
            data['products'] = InvoiceProductInlineFormset(self.request.POST, instance=self.object) 
        else:
             data['products'] = InvoiceProductInlineFormset(instance=self.object, queryset=InvoiceProduct.objects.filter(invoice=self.object))
        return data


    def get_form_class(self):
        print("Using UPDATE VIEW")  # Debug print
        return InvoiceUpdateForm
    
    def form_valid(self, form):
        print("Entering form_valid")
        print("Form data:", form.cleaned_data)
        context = self.get_context_data()
        products = context['products']
        print("Form valid:", form.is_valid())
        print("Products valid:", products.is_valid())
        if not products.is_valid():
            print("Products errors:", products.errors)  # Add this
            print("Non-form errors:", products.non_form_errors())  # And this
        if form.is_valid() and products.is_valid():
            print("Both form and products are valid")
            self.object = form.save()
            products.instance = self.object
            products.save()
            print("Save completed")
            return super().form_valid(form)
        print("Form validation failed")
        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be edited!', extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)

# Delete an Invoice
class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully deleted."

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be deleted!', extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)


InvoiceProductInlineFormset = inlineformset_factory(
    Invoice, InvoiceProduct,
    fields=['product', 'quantity', 'unit_price', 'reduction_rate', 'vat_rate'],
    extra=1,  # Number of empty forms to display
    can_delete=True
)

# Invoice details view for AJAX request
class InvoiceDetailsView(View):
    def get(self, request):
        invoice_id = request.GET.get('invoice_id')
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            products = invoice.products.all()
            product_data = [
                {
                    'name': product.product.name,
                    'unit_price': f"{product.unit_price:,.2f}",
                    'quantity': product.quantity,
                    'vat_rate': f"{product.vat_rate}%",  # Add VAT Rate
                    'reduction_rate': product.reduction_rate,
                    'raw_price': f"{product.quantity * product.unit_price * (1 - product.reduction_rate / 100):,.2f}",
                } for product in products
            ]

            # Calculate total raw amount
            total_raw_amount = sum([
                product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                for product in products
            ])

            # Calculate subtotal per VAT rate
            vat_subtotals = {}
            for product in products:
                vat_rate = product.vat_rate
                raw_price = product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                if vat_rate not in vat_subtotals:
                    vat_subtotals[vat_rate] = 0
                vat_subtotals[vat_rate] += raw_price * (vat_rate / 100)

            response_data = {
                'products': product_data,
                'total_raw_amount': f"{total_raw_amount:,.2f}",  # Add Total Raw Amount
                'vat_subtotals': [{'vat_rate': f"{rate}%", 'subtotal': f"{subtotal:,.2f}"} for rate, subtotal in vat_subtotals.items()],  # Add VAT Subtotals
                'total_vat': f"{invoice.total_tax_amount:,.2f}",
                'total_amount': f"{invoice.total_amount:,.2f}",
            }
            return JsonResponse(response_data)
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'Invoice not found'}, status=404)

# Product Autocomplete View
def product_autocomplete(request):
    query = request.GET.get('term', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(fiscal_label__icontains=query)
    )[:10]
    
    product_list = [{
        "label": f"{product.name} ({product.fiscal_label})",
        "value": product.id
    } for product in products]
    
    if not products:
        product_list.append({
            "label": f"Create new product: {query}",
            "value": "new"
        })
        
    return JsonResponse(product_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class EditProductInInvoiceView(View):
    def get(self, request, pk):
        """
        Handles loading the product data for editing.
        """
        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)
            # Prepare product data to return
            product_data = {
                'product': invoice_product.product.name,
                'product_name': invoice_product.product.name,
                'quantity': invoice_product.quantity,
                'unit_price': float(invoice_product.unit_price),
                'vat_rate': float(invoice_product.vat_rate),
                'reduction_rate': float(invoice_product.reduction_rate),
                'expense_code': invoice_product.product.expense_code,
                'fiscal_label': invoice_product.product.fiscal_label 
            }
            return JsonResponse(product_data, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        """
        Handles updating the product information.
        """
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate')

        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Update the fields with the provided data
            invoice_product.quantity = quantity
            invoice_product.unit_price = unit_price
            invoice_product.vat_rate = vat_rate
            invoice_product.reduction_rate = reduction_rate
            invoice_product.save()

            # Success response
            return JsonResponse({"message": "Product updated successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        """
        Handles deleting the product from the invoice.
        """
        try:
            # Fetch the InvoiceProduct instance
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Delete the instance
            invoice_product.delete()

            # Success response
            return JsonResponse({"message": "Product deleted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportInvoicesView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_export_invoice')

    def generate_excel(self, invoices):
        wb = Workbook()
        ws = wb.active
        ws.title = "Accounting Entries"

        # Define styles
        header_style = {
            'font': Font(bold=True, color='FFFFFF'),
            'fill': PatternFill(start_color='344960', end_color='344960', fill_type='solid'),
            'alignment': Alignment(horizontal='center', vertical='center'),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }

        # Set headers
        headers = ['Date', 'Label', 'Debit', 'Credit', 'Account Code', 'Reference', 'Journal', 'Counterpart']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_style['font']
            cell.fill = header_style['fill']
            cell.alignment = header_style['alignment']
            cell.border = header_style['border']

        # Set column widths
        ws.column_dimensions['A'].width = 12  # Date
        ws.column_dimensions['B'].width = 40  # Label
        ws.column_dimensions['C'].width = 15  # Debit
        ws.column_dimensions['D'].width = 15  # Credit
        ws.column_dimensions['E'].width = 15  # Account Code
        ws.column_dimensions['F'].width = 15  # Reference
        ws.column_dimensions['G'].width = 10  # Journal
        ws.column_dimensions['H'].width = 15  # Counterpart

        current_row = 2
        for invoice in invoices:
            entries = invoice.get_accounting_entries()
            for entry in entries:
                ws.cell(row=current_row, column=1, value=entry['date'].strftime('%d/%m/%Y'))
                ws.cell(row=current_row, column=2, value=entry['label'])
                ws.cell(row=current_row, column=3, value=entry['debit'])
                ws.cell(row=current_row, column=4, value=entry['credit'])
                ws.cell(row=current_row, column=5, value=entry['account_code'])
                ws.cell(row=current_row, column=6, value=entry['reference'])
                ws.cell(row=current_row, column=7, value=entry['journal'])
                ws.cell(row=current_row, column=8, value=entry['counterpart'])

                # Style number cells
                for col in [3, 4]:  # Debit and Credit columns
                    cell = ws.cell(row=current_row, column=col)
                    cell.number_format = '# ##0.00'
                    cell.alignment = Alignment(horizontal='right')

                current_row += 1

        return wb

    def post(self, request):
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            invoices = Invoice.objects.filter(id__in=invoice_ids, exported_at__isnull=True)

            if not invoices:
                return JsonResponse({'error': 'No valid invoices to export'}, status=400)

            # Generate Excel file
            wb = self.generate_excel(invoices)

            # Create export record
            export_record = ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'accounting_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )

            # Mark invoices as exported
            for invoice in invoices:
                invoice.exported_at = timezone.now()
                invoice.export_history.add(export_record)
                invoice.save()

            # Prepare response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{export_record.filename}"'
            wb.save(response)

            return response

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UnexportInvoiceView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_unexport_invoice')

    def post(self, request, invoice_id):
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            if not invoice.exported_at:
                return JsonResponse({'error': 'Invoice is not exported'}, status=400)

            # Create export record for the unexport action
            ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'unexport_{invoice.ref}_{timezone.now().strftime("%Y%m%d_%H%M%S")}',
                note=f'Unexported by {request.user.username}'
            )

            # Clear export date
            invoice.exported_at = None
            invoice.save()

            return JsonResponse({'message': 'Invoice successfully unexported'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class InvoicePaymentDetailsView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        payment_details = invoice.get_payment_details()
        
        # Get all related checks with their details
        checks = Check.objects.filter(cause=invoice).select_related('checker')
        check_details = [{
            'id': str(check.id),
            'reference': f"{check.checker.bank}-{check.position}",
            'amount': float(check.amount),
            'status': check.status,
            'created_at': check.creation_date.strftime('%Y-%m-%d'),
            'delivered_at': check.delivered_at.strftime('%Y-%m-%d') if check.delivered_at else None,
            'paid_at': check.paid_at.strftime('%Y-%m-%d') if check.paid_at else None,
        } for check in checks]

        return JsonResponse({
            'payment_details': payment_details,
            'checks': check_details
        })
```

# testapp/views_product.py

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product
from .forms import ProductForm
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.db import models
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        product = self.get_object()
        print("Current VAT rate:", product.vat_rate)  # Debug print
        print("Form VAT rate:", form.initial.get('vat_rate'))  # Debug print
        return form

    def get_initial(self):
        initial = super().get_initial()
        product = self.get_object()
        print("Initial VAT rate:", product.vat_rate)  # Debug print
        initial['vat_rate'] = product.vat_rate
        return initial

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoiceproduct_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoiceproduct_set.count()} invoice(s).')
            return redirect('product-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete product. It is referenced by one or more invoices.')
            return redirect('product-list')


# AJAX view for creating a new Product
@method_decorator(csrf_exempt, name='dispatch')
class ProductAjaxCreateView(View):
    def post(self, request):
        try:
            name = request.POST.get('name')
            # Check for existing product with same name
            if Product.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'error': f'A product with the name "{name}" already exists.'
                }, status=400)

            product = Product.objects.create(
                name=name,
                fiscal_label=request.POST.get('fiscal_label'),
                is_energy=request.POST.get('is_energy') == 'true',
                expense_code=request.POST.get('expense_code'),
                vat_rate=request.POST.get('vat_rate')
            )
            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(product.id)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailsView(View):
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            return JsonResponse({
                'expense_code': product.expense_code,
                'vat_rate': str(product.vat_rate)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


```

# testapp/views_supplier.py

```py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Supplier
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = 'supplier/supplier_list.html'
    context_object_name = 'suppliers'

# Create a new Supplier
class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully created."

# Update an existing Supplier
class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully updated."


# Delete a Supplier
class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'supplier/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoice_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoice_set.count()} invoice(s).')
            return redirect('supplier-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete supplier. It is referenced by one or more invoices.')
            return redirect('supplier-list')

```

# testapp/views.py

```py
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView


# Create your views here.
def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # Redirect to the profile view after successful login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')  # Render the login template

@never_cache
@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def profile(request):
    return render(request, 'profile.html')  # Use 'profile.html' directly


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Welcome, {form.get_user().first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Custom logout view to prevent back button access after logout
@cache_control(no_cache=True, must_revalidate=True)
def logout_view(request):
    logout(request)
    # Redirect to the login page after logout
    response = HttpResponseRedirect('/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
```

