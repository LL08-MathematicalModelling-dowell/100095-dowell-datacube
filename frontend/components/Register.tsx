import { Button, Fieldset, Input, Stack } from "@chakra-ui/react";
import { Field } from "@/components/ui/field";
// import { NativeSelectField, NativeSelectRoot } from "@/components/ui/native-select";

function RegistrationForm() {
  return (
    <Fieldset.Root size="lg" maxW="md">
      <Stack>
        <Fieldset.Legend>Registration Form</Fieldset.Legend>
        <Fieldset.HelperText>Please fill in the details below to register.</Fieldset.HelperText>
      </Stack>

      <Fieldset.Content>
        <Field label="Username">
          <Input name="username" placeholder="Enter your username" />
        </Field>

        <Field label="Email Address">
          <Input name="email" type="email" placeholder="Enter your email" />
        </Field>

        <Field label="Password">
          <Input name="password" type="password" placeholder="Enter your password" />
        </Field>

        <Field label="Country">
          {/* <NativeSelectRoot>
            <NativeSelectField
              name="country"
              items={["United States", "Canada", "United Kingdom"]}
            />
          </NativeSelectRoot> */}
        </Field>
      </Fieldset.Content>

      <Button type="submit" alignSelf="flex-start">
        Register
      </Button>
    </Fieldset.Root>
  );
}

export default RegistrationForm;
