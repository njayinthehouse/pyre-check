// Copyright 2004-present Facebook. All Rights Reserved.

package com.facebook.buck_project_builder.util;

import org.junit.Test;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class FileSystemTest {

  private static void writeContent(File file, String content) throws IOException {
    try (FileWriter writer = new FileWriter(file)) {
      writer.write(content + "\n");
      writer.flush();
    }
  }

  private static void assertIsSymbolicLinkWithContent(Path symbolicLinkPath, String expectedContent) throws IOException {
    assertTrue(
            "after symbolic link creation, symbolicLinkPath should actually be a symbolic link",
            Files.isSymbolicLink(symbolicLinkPath));
    try (BufferedReader reader = new BufferedReader(new FileReader(symbolicLinkPath.toFile()))) {
      assertEquals(reader.readLine(), expectedContent);
    }
  }

  @Test
  public void addSymbolicLinkTest() throws IOException {
    Path tempDirPath = Files.createTempDirectory("symbolic_link_test");
    Path actualPath = Paths.get(tempDirPath.toString(), "a.txt");
    Path symbolicLinkPath = Paths.get(tempDirPath.toString(), "a/b/c/link");

    assertFalse("symbolic link does not exist yet", symbolicLinkPath.toFile().exists());
    writeContent(actualPath.toFile(), "abc");
    FileSystem.addSymbolicLink(symbolicLinkPath, actualPath);
    assertIsSymbolicLinkWithContent(symbolicLinkPath, "abc");

    // the operation above makes the symbolic link appear.
    assertTrue("symbolic link should already be there", symbolicLinkPath.toFile().exists());
    writeContent(actualPath.toFile(), "def");
    FileSystem.addSymbolicLink(symbolicLinkPath, actualPath);
    assertIsSymbolicLinkWithContent(symbolicLinkPath, "def");
  }
}
