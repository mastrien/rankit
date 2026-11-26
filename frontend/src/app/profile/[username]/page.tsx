import { ProfileView } from "@/components/profile/ProfileView";

interface ProfilePageProps {
  readonly params: Promise<{ readonly username: string }>;
}

/** Dynamic public profile page for /profile/[username]. */
export default async function ProfilePage({ params }: ProfilePageProps) {
  const { username } = await params;
  return <ProfileView username={username} />;
}
