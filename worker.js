export default {
  async fetch(request, env) {
    return handleRequest(request, { env });
  }
};

// Helper function to get existing user
async function getExistingUser(userEmail, env) {
  console.log(`Searching for user with email: ${userEmail}`);
  
  try {
    const response = await fetch(
      `https://api.eu.cryptlex.com/v3/users?email=${encodeURIComponent(userEmail)}`,
      {
        headers: {
          "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to get user by email: ${errorText}`);
      throw new Error(`Failed to get user by email: ${errorText}`);
    }

    const users = await response.json();
    console.log(`Found ${users.length} users with email ${userEmail}`);
    
    if (users && users.length > 0) {
      const exactMatch = users.find(user => user.email.toLowerCase() === userEmail.toLowerCase());
      if (exactMatch) {
        console.log('Found user with exact email match:', exactMatch);
        return exactMatch;
      }
      console.log('No exact email match found, will create a new user');
    }
    
    throw new Error(`No user found with email: ${userEmail}`);
  } catch (error) {
    console.error('Error finding user:', error);
    throw error;
  }
}

// Helper function to generate a random password
function generateRandomPassword() {
  const length = 12;
  const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+";
  let password = "";
  
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * charset.length);
    password += charset[randomIndex];
  }
  
  return password;
}

// Helper function to create user
async function createUser(userEmail, firstName, lastName, orgId, env) {
  console.log('Creating user with:', {
    email: userEmail,
    firstName: firstName,
    lastName: lastName,
    organizationId: orgId
  });

  const response = await fetch(
    "https://api.eu.cryptlex.com/v3/users",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email: userEmail,
        firstName: firstName,
        lastName: lastName || "",
        password: generateRandomPassword(),
        role: "user",
        organizationId: orgId
      })
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('User creation failed:', errorText);
    throw new Error(`Failed to create user: ${errorText}`);
  }

  const user = await response.json();
  console.log('User created successfully:', user);
  return user;
}

// Helper function to get existing organization
async function getExistingOrganization(orgEmail, env) {
  console.log(`Searching for organization with exact email: ${orgEmail}`);
  
  try {
    const response = await fetch(
      `https://api.eu.cryptlex.com/v3/organizations?email=${encodeURIComponent(orgEmail)}`,
      {
        headers: {
          "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to get organization by email: ${errorText}`);
      throw new Error(`Failed to get organization by email: ${errorText}`);
    }

    const orgs = await response.json();
    console.log(`Found ${orgs.length} organizations with email ${orgEmail}`);
    
    if (orgs && orgs.length > 0) {
      const exactMatch = orgs.find(org => org.email.toLowerCase() === orgEmail.toLowerCase());
      if (exactMatch) {
        console.log('Found organization with exact email match:', exactMatch);
        return exactMatch;
      }
      console.log('No exact email match found, will create a new organization');
    }
    
    throw new Error(`No organization found with email: ${orgEmail}`);
  } catch (error) {
    console.error('Error finding organization:', error);
    throw error;
  }
}

// Helper function to create organization
async function createOrganization(orgEmail, env) {
  const orgDomain = orgEmail.split('@')[1];
  const orgName = orgDomain.split('.')[0].toUpperCase();
  
  console.log('Creating organization with:', {
    name: orgName,
    email: orgEmail,
    domain: orgDomain,
    allowedUsers: 500
  });

  const response = await fetch(
    "https://api.eu.cryptlex.com/v3/organizations",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name: orgName,
        email: orgEmail,
        domain: orgDomain,
        allowedUsers: 500,
        description: `Organization for ${orgDomain} domain users`
      })
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Organization creation failed:', errorText);
    throw new Error(`Failed to create organization: ${errorText}`);
  }

  const org = await response.json();
  console.log('Organization created successfully:', org);
  return org;
}

// Helper function to create license (Updated to include productVersionId)
async function createLicense(userId, productId, productVersionId, organization, userName, env) {
  console.log('Creating license for:', {
    userId: userId,
    productId: productId,
    productVersionId: productVersionId,
    organizationName: organization.name,
    userName: userName
  });

  const response = await fetch(
    "https://api.eu.cryptlex.com/v3/licenses",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        userId: userId,
        productId: productId,
        productVersionId: productVersionId, // Added
        type: "node-locked",
        validity: 30 * 86400, // 30 days in seconds
        metadata: [
          { key: "organizationName", value: organization.name, visible: true },
          { key: "userName", value: userName, visible: true },
          { key: "productVersionId", value: productVersionId, visible: true } // Added for visibility
        ]
      })
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('License creation failed:', errorText);
    throw new Error(`Failed to create license: ${errorText}`);
  }

  const license = await response.json();
  console.log('License created successfully:', license);
  return license;
}

// Helper function to validate email domains
function validateEmailDomains(orgEmail, userEmail) {
  if (!orgEmail || !userEmail) {
    throw new Error('Both organization email and user email are required');
  }
  
  const orgDomain = orgEmail.split('@')[1].toLowerCase();
  const userDomain = userEmail.split('@')[1].toLowerCase();
  
  console.log('Validating email domains:', {
    orgDomain: orgDomain,
    userDomain: userDomain
  });
  
  const specialDomains = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com'];
  
  if (specialDomains.includes(orgDomain)) {
    console.log('Organization email is from a special domain, skipping domain validation');
    return true;
  }
  
  if (orgDomain !== userDomain) {
    throw new Error(`Email domains don't match: org=${orgDomain}, user=${userDomain}`);
  }
  
  return true;
}

// Helper: Extract email from User Info
function extractEmailFromUserInfo(userInfo) {
  const match = userInfo.match(/\((.+)\)$/);
  if (!match) {
    throw new Error(`Failed to extract email from User Info: ${userInfo}`);
  }
  return match[1];
}

// Helper: Fetch Subscription from Stripe API
async function fetchStripeSubscription(subscriptionId, stripeSecretKey) {
  const response = await fetch(
    `https://api.stripe.com/v1/subscriptions/${subscriptionId}`,
    {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${stripeSecretKey}`,
        "Content-Type": "application/json"
      }
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Failed to fetch Stripe subscription: ${errorText}`);
    throw new Error(`Failed to fetch Stripe subscription: ${errorText}`);
  }

  const subscription = await response.json();
  console.log('Fetched Stripe subscription:', subscription);
  return subscription;
}

// Helper: Update Subscription Metadata in Stripe
async function updateSubscriptionMetadata(subscriptionId, metadata, stripeSecretKey) {
  console.log(`Updating subscription ${subscriptionId} with metadata:`, metadata);
  
  const response = await fetch(
    `https://api.stripe.com/v1/subscriptions/${subscriptionId}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${stripeSecretKey}`,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: new URLSearchParams({
        "metadata[User Info]": metadata["User Info"],
        "metadata[productId]": metadata["productId"],
        "metadata[organizationEmail]": metadata["organizationEmail"],
        "metadata[licenseId]": metadata["licenseId"]
      }).toString()
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Failed to update subscription metadata: ${errorText}`);
    throw new Error(`Failed to update subscription metadata: ${errorText}`);
  }

  const updatedSubscription = await response.json();
  console.log('Subscription metadata updated successfully:', updatedSubscription);
  return updatedSubscription;
}

// Helper: Renew license (using POST /renew with minimal body)
async function renewLicense(licenseId, env) {
  console.log(`Renewing license: ${licenseId}`);
  console.log(`Using CRYPTLEX_TOKEN: ${env.CRYPTLEX_TOKEN}`);
  
  const headers = {
    "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`,
    "Content-Type": "application/json"
  };
  console.log('Request headers:', headers);

  const response = await fetch(
    `https://api.eu.cryptlex.com/v3/licenses/${licenseId}/renew`,
    {
      method: "POST",
      headers: headers,
      body: JSON.stringify({})
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Failed to renew license: ${errorText}`);
    throw new Error(`Failed to renew license: ${errorText}`);
  }

  const updatedLicense = await response.json();
  console.log('License renewed successfully:', updatedLicense);
  return updatedLicense;
}

// Helper: Extend license (for expired licenses)
async function extendLicense(licenseId, extensionLength, env) {
  console.log(`Extending license ${licenseId} by ${extensionLength} days`);
  const headers = { "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`, "Content-Type": "application/json" };
  const response = await fetch(
    `https://api.eu.cryptlex.com/v3/licenses/${licenseId}/extend`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ extensionLength: extensionLength * 86400 }) // Convert days to seconds
    }
  );
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Failed to extend license: ${errorText}`);
    throw new Error(`Failed to extend license: ${errorText}`);
  }
  const updatedLicense = await response.json();
  console.log('License extended successfully:', updatedLicense);
  return updatedLicense;
}

// Handle checkout session (initial subscription) - Updated to pass productVersionId
async function handleCheckoutSession(payload, env) {
  const metadata = payload.data?.object?.metadata || {};
  console.log('Processing checkout session with metadata:', metadata);
  
  if (!metadata.organizationEmail || !metadata.userEmail || !metadata.productId || !metadata.productVersionId) {
    throw new Error('Missing required metadata');
  }

  validateEmailDomains(metadata.organizationEmail, metadata.userEmail);

  let organization;
  try {
    console.log('Attempting to find existing organization...');
    organization = await getExistingOrganization(metadata.organizationEmail, env);
    console.log('Found existing organization:', organization);
  } catch (error) {
    console.log('No existing organization found, creating new one...');
    organization = await createOrganization(metadata.organizationEmail, env);
  }

  let user;
  try {
    console.log('Attempting to find existing user...');
    user = await getExistingUser(metadata.userEmail, env);
    console.log('Found existing user:', user);
  } catch (error) {
    console.log('No existing user found, creating new one...');
    user = await createUser(
      metadata.userEmail, 
      metadata.firstName, 
      metadata.lastName || '', 
      organization.id, 
      env
    );
  }

  console.log('Creating license...');
  const userName = `${metadata.firstName} ${metadata.lastName || ''}`.trim();
  const license = await createLicense(
    user.id,
    metadata.productId,
    metadata.productVersionId, // Added
    organization,
    userName,
    env
  );
  console.log('License created:', license);

  // Update Stripe Subscription metadata with licenseId
  const subscriptionId = payload.data.object.subscription;
  if (subscriptionId) {
    const subscriptionMetadata = {
      "User Info": `${metadata.firstName} ${metadata.lastName || ''} (${metadata.userEmail})`,
      "productId": metadata.productId,
      "organizationEmail": metadata.organizationEmail,
      "licenseId": license.id
    };
    await updateSubscriptionMetadata(subscriptionId, subscriptionMetadata, env.STRIPE_SECRET_KEY);
  } else {
    console.error('No subscription ID found in checkout payload');
  }

  return {
    organization: organization,
    user: user,
    licenseId: license.id,
    licenseKey: license.key
  };
}

// Handle renewal
async function handleRenewal(event, env) {
  console.log('Processing renewal event:', event);

  const subscriptionId = event.data.object.subscription;
  const billingReason = event.data.object.billing_reason;

  if (billingReason === "subscription_create") {
    console.log('Skipping initial invoice payment');
    return {
      success: true,
      message: 'Initial payment ignored - license already created'
    };
  }

  const subscription = await fetchStripeSubscription(subscriptionId, env.STRIPE_SECRET_KEY);
  const userInfo = subscription.metadata["User Info"];
  const licenseId = subscription.metadata["licenseId"];
  if (!userInfo || !licenseId) {
    throw new Error('User Info or licenseId metadata missing from subscription');
  }

  const userEmail = extractEmailFromUserInfo(userInfo);
  console.log(`Extracted user email for renewal: ${userEmail}`);
  console.log(`Processing license ID: ${licenseId}`);

  // Fetch license details to check expiry
  const licenseResponse = await fetch(
    `https://api.eu.cryptlex.com/v3/licenses/${licenseId}`,
    { headers: { "Authorization": `Bearer ${env.CRYPTLEX_TOKEN}`, "Content-Type": "application/json" } }
  );
  if (!licenseResponse.ok) {
    const errorText = await licenseResponse.text();
    console.error(`Failed to fetch license details: ${errorText}`);
    throw new Error(`Failed to fetch license details: ${errorText}`);
  }
  const license = await licenseResponse.json();
  const expiresAt = new Date(license.expiresAt).getTime() / 1000; // Convert to Unix timestamp (seconds)
  const now = Math.floor(Date.now() / 1000); // Current time in seconds
  const gracePeriod = 1 * 86400; // 1 day in seconds

  if (expiresAt >= now - gracePeriod) {
    // Active license (or within grace period)
    console.log(`License ${licenseId} is active or within grace, renewing`);
    await renewLicense(licenseId, env);
    return { success: true, licenseId: licenseId, message: 'License extended successfully' };
  } else {
    // Expired license (past grace period)
    const daysSinceExpiry = Math.floor((now - expiresAt) / 86400); // Days since expiry
    const extensionDays = daysSinceExpiry + 30; // Days expired + 30 days
    console.log(`License ${licenseId} expired ${daysSinceExpiry} days ago, extending by ${extensionDays} days`);
    await extendLicense(licenseId, extensionDays, env);
    return { success: true, licenseId: licenseId, message: `License extended by ${extensionDays} days from expiry` };
  }
}

// Main fetch handler
async function handleRequest(request, event) {
  const { pathname } = new URL(request.url);
  
  if (request.method === "GET") {
    return new Response(
      JSON.stringify({ status: "healthy", message: "Webhook endpoint is running" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }
  
  if (request.method === "POST" && (pathname === "/" || pathname === "/webhook")) {
    try {
      const payload = await request.json();
      console.log('Received webhook payload:', payload);
      
      if (payload.type === 'checkout.session.completed') {
        console.log('Processing checkout.session.completed event');
        const result = await handleCheckoutSession(payload, event.env);
        
        return new Response(JSON.stringify({
          success: true,
          organizationId: result.organization.id,
          userId: result.user.id,
          licenseId: result.licenseId,
          licenseKey: result.licenseKey,
          message: 'License created successfully'
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      } else if (payload.type === 'invoice.payment_succeeded') {
        console.log('Processing invoice.payment_succeeded event');
        const result = await handleRenewal(payload, event.env);
        
        return new Response(JSON.stringify({
          success: result.success,
          licenseId: result.licenseId || null,
          message: result.message
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify({
        success: true,
        message: `Event type ${payload.type} received but not processed`
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('Error handling request:', error);
      return new Response(JSON.stringify({
        success: false,
        error: error.message,
        message: 'Failed to process webhook'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  return new Response('Method Not Allowed', { status: 405 });
}