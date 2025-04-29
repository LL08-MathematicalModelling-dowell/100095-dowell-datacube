import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import bcrypt from "bcryptjs";
import { prisma } from "@/prisma/client";

// Define input validation schema
const schema = z.object({
  email: z.string().email(),
  firstName: z.string().min(3),
  lastName: z.string().min(3),
  password: z.string().min(5),
});

export async function POST(request: NextRequest) {
  try {
    // Parse and validate the request body
    const body = await request.json();
    console.log("Request Body:", JSON.stringify(body));
    const validation = schema.safeParse(body);
    console.log(`Validation >>><<<<     : ${validation.success}`);

    if (!validation.success) {
      console.error("Validation errors:", validation.error.errors);
      return NextResponse.json(
        { errors: validation.error.errors },
        { status: 400 }
      );
    }

    const { email, firstName, lastName, password } = validation.data;

    // Check if the user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return NextResponse.json(
        { error: "User already exists" },
        { status: 400 }
      );
    }

    // Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Combine firstName and lastName to create 'name'
    const fullName = `${firstName} ${lastName}`;

    // Create the new user
    const newUser = await prisma.user.create({
      data: {
        email,
        name: fullName, // Store the combined name
        hashedPassword,
      },
    });

    // Respond with user data (excluding sensitive fields)
    return NextResponse.json(
      {
        message: "User created successfully",
        user: {
          id: newUser.id,
          email: newUser.email,
          name: newUser.name,
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error during user registration:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
