import { EditProfileForm } from "@/components/profile/EditProfileForm";

/** Page for editing the authenticated user's Rankit profile. */
export default function EditProfilePage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-10">
      <EditProfileForm />
    </section>
  );
}
