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
