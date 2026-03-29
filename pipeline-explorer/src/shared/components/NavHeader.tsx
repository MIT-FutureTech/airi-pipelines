"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./NavHeader.module.css";

const navItems = [
  { href: "/", label: "Pipeline Graph" },
  { href: "/airtable", label: "Airtable" },
];

export function NavHeader() {
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <div>
        <h1 className={styles.title}>AIRI Pipeline Explorer</h1>
        <p className={styles.subtitle}>
          Interactive map of the AI Risk Initiative data pipelines.
        </p>
      </div>
      <nav className={styles.nav}>
        {navItems.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`${styles.navLink} ${pathname === href ? styles.navLinkActive : ""}`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
